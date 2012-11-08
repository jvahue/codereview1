"""
Violation DB
This file implements the Violation DB.  Any violation detected by any tool is reported here for
analysis.  The analysis performed can be recorded to identify who did it, when they did it and what
their analysis was.
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import csv
import os
import re

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
from utils.DB.sqlLite.database import DB_SQLite

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eDbRoot = r'db'
eDbName = r'KsCrDb.db'

eNotReported = 'Not Reported'
eAutoWho = 'Auto'

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
class ViolationDb( DB_SQLite):
    #-----------------------------------------------------------------------------------------------
    def __init__( self, projRoot):
        """ Create an instance of the violation DB
        """
        DB_SQLite.__init__( self)
        self.dbPath = os.path.join( projRoot, eDbRoot)
        self.dbName = os.path.join( self.dbPath, eDbName)
        if not os.path.isdir( self.dbPath):
            try:
                os.makedirs( self.dbPath)
            except OSError:
                # some one running in parallel must have beat us to it
                pass

        # does the DB already exist
        dbExists = os.path.isfile( self.dbName)

        self.Open()
        if not dbExists or 1:
            fields = ( 'filename text',
                       'function text',
                       'severity text',
                       'violationId text',
                       'description text',
                       'details text',
                       'lineNumber integer',  # not primary as this will change over time
                       'detectedBy text',
                       'firstReport timestamp',
                       'lastReport timestamp',
                       'status text',
                       'analysis text',
                       'who text',
                       'reviewDate timestamp',
                       'primary key (filename,function,severity,violationId,description,details,lineNumber)',
                       )
            query  = 'CREATE TABLE if not exists Violations(%s)' % ','.join(fields)
            if self.Execute(query):
                self.Commit()

        self.insertNew = 0
        self.insertUpdate = 0
        self.insertSelErr = 0
        self.insertInErr = 0
        self.insertUpErr = 0

        # merge stats
        self.mergePct = 0        # percent complete with merge
        self.mergeInsert = 0     # how many new records did we insert
        self.mergeUpdate = 0     # how many existing records did we update
        self.mergeInsertFail = 0 # how many inserts failed
        self.mergeUpdateFail = 0 # how many merge updates failed

        self.noAnalysis = 0      # how many have no analysis
        self.selfAnalysis = 0    # haw many chose the main db analysis
        self.mergeAnalysis = 0   # how many analysis came from the merge db
        self.bothAnalysis = 0    # how many are a merge of the to analysis

    #-----------------------------------------------------------------------------------------------
    def Open( self):
        self.Connect( self.dbName)

    #-----------------------------------------------------------------------------------------------
    def Insert( self, fName, func, sev, violationId, desc, details, line, detectedBy, updateTime):
        """ Insert a violation into the DB.
            If entry exists
                update lineNumber and description
                copy analysis if it exists
            else
                insert new row
        """
        func = func.strip()
        if func == '':
            func = 'N/A'

        details = details.strip()
        if details == '':
            details = 'N/A'
        else:
            # remove space to eliminate diffs
            detail0 = details.replace('  ', ' ')
            while detail0 != details:
                details = detail0
                detail0 = details.replace('  ',' ')

        matchItem = self.IsNewRecord(fName, func, sev, violationId,
                                     desc, details, line, detectedBy, updateTime)
        if matchItem is None:
            d = (fName, func, sev, violationId, desc, details, line, detectedBy,updateTime,updateTime)
            s = """
                insert into Violations
                (filename,function,severity,violationId,description,details,lineNumber,detectedBy,firstReport,lastReport)
                values (%s)
                """ % ','.join('?'*len(d))
            #if self.Execute( s, fName, func, sev, violationId, desc, details, line, detectedBy, updateTime, updateTime) != 1:
            if self.Execute( s, *d) != 1:
                self.insertInErr += 1
            else:
                self.insertNew += 1
        else:
            sts = matchItem.status
            stsDate = matchItem.reviewDate
            analysis = matchItem.analysis
            who = matchItem.who
            # if it was 'Not Reported' and has come back clear analysis out
            if sts == eNotReported:
                sts = None
                who = None
                stsDate = None
                analysis = None

            updateItems = (updateTime, desc, details, line, sts, who, stsDate, analysis)
            primary = (fName, func, sev, violationId,
                       matchItem.description, matchItem.details, matchItem.lineNumber)
            s = """
                update Violations
                set lastReport=?, description=?, details=?, lineNumber=?,
                    status = ?, who=?, reviewDate=?, who=?
                where
                filename=?
                and function=?
                and severity=?
                and violationID=?
                and description=?
                and details=?
                and lineNumber=?
                """
            params = updateItems + primary
            if self.Execute( s, *params) != 1:
                self.insertUpErr += 1
            else:
                self.insertUpdate += 1

    #-----------------------------------------------------------------------------------------------
    def IsNewRecord( self, fName, func, sev, violId, desc, details, line, detectedBy, updateTime):
        """ Check to see if the record is new to the DB, if not return the matching record
            and there better only be one.

            Returns: the matching row in the DB as matchItem
        """
        # debug hook
        fnM = fName==r'application\EngineRun.c'
        fcM = func=='N/A'
        if fnM and fcM and sev=='Error'and violId =='FileFmt-FileName':
            pass

        # determine if this violation already exists in the DB
        s = """
            select filename,function,severity,violationId,description,details,lineNumber,
                   detectedBy,firstReport,lastReport,status,analysis,who,reviewDate
            from Violations where
            filename=?
            and function=?
            and severity=?
            and violationId=?
            and detectedBy=?
            and details=?
            and lastReport!=?
            """

        data0 = self.Query( s, fName, func, sev, violId, detectedBy, details, updateTime)
        if data0 is None:
            # Query failed - default to no match
            self.insertSelErr += 1
            data0 = []

        matchedItem = None
        if len(data0) > 0:
            # create a regex of all line numbers in the description
            descriptionRe = re.compile(self.GetDescriptionRe( desc))

            # pre-filter data set for our description
            # having us do this (vs. the DB with like) speeds things up a lot
            data = [i for i in data0 if descriptionRe.search(i.description)]

            if len(data) != len(data0):
                pass

            if len(data) > 0:
                matchLineNumber = True
                # check some conditions
                # if multiple row with the same line number don't match on LineNumber
                lineNumbers = {}
                for i in data:
                    lineNumbers[i.lineNumber] = lineNumbers.get( i.lineNumber, 0) + 1
                    if lineNumbers[i.lineNumber] > 1:
                        matchLineNumber = False
                        break

                # scan through the description and check for matches
                #   convert line numbers to regex for comparison
                for i in data:
                    m = descriptionRe.search(i.description)
                    # if we match everything ...
                    if m and len(m.group(0)) == len(i.description):
                        lineMatch = (matchLineNumber and (int(line) == i.lineNumber))
                        descMatch = (not matchLineNumber and (desc == i.description))
                        # give preference to a lineNumber/desc match, then first in/first out
                        # we need to run through all incase the linematch is later in the data set
                        if not matchedItem or lineMatch or descMatch:
                            matchedItem = i
        else:
            pass

        return matchedItem

    #-----------------------------------------------------------------------------------------------
    def Merge( self, mergeDbName):
        """ Merge the data from the other DB in with ours.  Merge rules are:

            for all rows in the mergeDb:
              if row match in selfDB:
                if no analysis in either: continue
                if analysis in one DB: insert that with credentials
                if analysis in both: append new to older and insert with newer credentials
                  - tag merged analysis for review format
                    MergeOld:
                      Old analysis
                    MergeNew:
                      NewAnalysis
              else:
                Insert the entire row from mergeDb
        """
        # merge stats
        self.mergePct = 0        # percent complete with merge
        self.mergeInsert = 0     # how many new records did we insert
        self.mergeUpdate = 0     # how many existing records did we update
        self.mergeInsertFail = 0 # how many inserts failed
        self.mergeUpdateFail = 0 # how many merge updates failed

        self.noAnalysis = 0      # how many have no analysis
        self.selfAnalysis = 0    # haw many chose the main db analysis
        self.mergeAnalysis = 0   # how many analysis came from the merge db
        self.bothAnalysis = 0    # how many are a merge of the to analysis

        self.myCount = 0
        self.size = 0

        s = 'select count(*) from violations'
        myCount = self.GetOne(s)
        if myCount:
            self.myCount = myCount[0]

        # TODO handle big DB's, right now we are in the 20-25k rows so just it all in mem
        s = """
            select filename,function,severity,violationId,description,details,lineNumber,
                   detectedBy,firstReport,lastReport,status,analysis,who,reviewDate
            from Violations
            """
        odb = DB_SQLite()
        odb.Connect( mergeDbName)
        mergeData = odb.Query( s)

        self.size = len(mergeData)
        if self.size > 0:
            sizeInv = 100.0/self.size
        else:
            sizeInv = 100.0

        if self.size > 0:
            counter = 0
            self.mergePct = 0
            for r in mergeData:
                counter += 1
                self.mergePct = float(counter) * sizeInv

                matchItem = self.IsNewRecord(r.filename, r.function, r.severity, r.violationId,
                                             r.description, r.details, r.lineNumber, r.detectedBy,
                                             '')
                if matchItem:
                    # get all the analysis data
                    analysis, who, reviewDate, status = self.GetMergeAnalysis( r, matchItem)

                    # who's firstReport is less
                    if matchItem.firstReport < r.firstReport:
                        first = matchItem.firstReport
                    else:
                        first = r.firstReport

                    # who's data to insert based on lastReport date
                    if matchItem.lastReport > r.lastReport:
                        insert = matchItem
                    else:
                        insert = r

                    iData = (insert.filename, insert.function, insert.severity, insert.violationId,
                             insert.description, insert.details, insert.lineNumber, insert.detectedBy,
                             first, insert.lastReport, status, analysis, who, reviewDate)

                    primary = (matchItem.filename, matchItem.function, matchItem.severity,
                               matchItem.violationId, matchItem.description, matchItem.details,
                               matchItem.lineNumber)

                    s = """Update violations set
                             filename=?, function=?, severity=?, violationId=?,
                             description=?, details=?, lineNumber=?, detectedBy=?,
                             firstReport=?, lastReport=?, status=?, analysis=?, who=?, reviewDate=?
                           where
                             filename=? and function=? and severity=? and
                             violationID=? and description=? and details=? and
                             lineNumber=?
                           """

                    allData = iData + primary
                    if self.Execute( s, *allData) == 1:
                        self.mergeUpdate += 1
                    else:
                        self.mergeUpdateFail += 1

                else:
                    # selfDb does not have this record, insert the entire thing
                    d = (r.filename, r.function, r.severity, r.violationId, r.description, r.details,
                         r.lineNumber, r.detectedBy, r.firstReport, r.lastReport, r.status, r.analysis,
                         r.who, r.reviewDate)
                    s = """
                        insert into Violations (
                          filename, function, severity, violationId, description, details,
                          lineNumber, detectedBy, firstReport, lastReport, status, analysis,
                          who, reviewDate)
                        values (%s)
                        """ % ','.join('?'*len(d))
                    if self.Execute( s, *d) == 1:
                        self.mergeInsert += 1
                    else:
                        self.mergeInsertFail += 1

            # now save everything
            self.Commit()

    #-----------------------------------------------------------------------------------------------
    def GetMergeAnalysis( self, mergeItem, matchItem):
        """ create the analysis data to be merged
        returns all analysis fields
        """
        selfAnalysis = matchItem.reviewDate is not None
        mergeAnalysis = mergeItem.reviewDate is not None

        # check both exist
        if selfAnalysis and mergeAnalysis:
            self.bothAnalysis += 1
            # who's analysis is newer
            if matchItem.reviewDate > mergeItem.reviewDate:
                # self is newer
                newer = matchItem
                older = mergeItem
            else:
                # merge is newer
                older = matchItem
                newer = mergeItem

            # TODO fix this and make a table of analysis related to each violation row
            # right now for Not reported Analysis is None
            if newer.analysis and older.analysis:
                newHasOld = newer.analysis.find( older.analysis) != -1
                oldHasNew = older.analysis.find( newer.analysis) != -1
                if newHasOld or oldHasNew:
                    analysis = newer.analysis
                else:
                    analysis = 'MergeOld(%s/%s):\n%s\nMergeNew:\n%s' % (older.who,
                                                                        older.status,
                                                                        older.analysis,
                                                                        newer.analysis)
            elif newer.analysis:
                analysis = newer.analysis
            else:
                analysis = older.analysis

        elif selfAnalysis:
            self.selfAnalysis += 1
            analysis = matchItem.analysis
            newer = matchItem
        else:
            if mergeAnalysis:
                self.mergeAnalysis += 1
            else:
                self.noAnalysis += 1
            analysis = mergeItem.analysis
            newer = mergeItem

        return analysis, newer.who, newer.reviewDate, newer.status

    #-----------------------------------------------------------------------------------------------
    def ShowMergeStats(self):
        """ Display what happened during the last run """
        statNames = ('mergeInsert',
                     'insertUpdate',
                     'mergeUpdate',
                     'mergeInsertFail',
                     'mergeUpdateFail',
                     'noAnalysis',
                     'selfAnalysis',
                     'mergeAnalysis',
                     'bothAnalysis',
                     )

        self.mergeStats = ['Merge Stats\n']
        msg = 'PreMerge CurrentDB: %d records - MergeDB: %d records\n' % (self.myCount,
                                                                          self.size)
        self.mergeStats.append( msg)
        for i in statNames:
            self.mergeStats.append('%s: %s' % (i, str(getattr(self, i, -1))))

        return '\n'.join( self.mergeStats)

    #-----------------------------------------------------------------------------------------------
    def GetDescriptionRe( self, desc, sql=False):
        """ Turn all line number references into a regex search:
            Ignoring return value of function 'foo(void)' (compare with line 163, file xyz.h)
            Storage class of symbol 'foo(void *)' assumed static (line 150)

            desc: the string to modify
            sql: create a SQL wildcard search
        """
        lineRe = re.compile(r'[Ll]ine[ \t]+([0-9]+)')
        m = lineRe.findall( desc)

        if not sql:
            # escape special regex chars in the description
            # the '\' must be first so it only replaces itself when it in the original string
            for c in r'\.^$*+?{}[]|()':
                desc = desc.replace(c, r'\%s' % c)

        if m:
            # now put the number regex in
            wild = '%' if sql else '[0-9]+'
            for i in m:
                desc = desc.replace(i, wild)

        return desc

    #-----------------------------------------------------------------------------------------------
    def MarkNotReported( self, detectedBy, updateTime):
        """ mark all items not reported this run and return the count of those """
        # count how many will be marked
        s = """
            select count(*)
            from violations
            where lastReport != ?
            and detectedBy = '%s'
            and reviewDate is Null
            """ % (detectedBy,)
        self.Execute( s, updateTime)
        data = self.GetOne()

        # mark them as not being reported anymore
        s = """ update violations set
                status=?, reviewDate=?
                where lastReport != ?
                and detectedBy = '%s'
                and reviewDate is Null
            """ % (detectedBy)
        self.Execute( s, eNotReported, updateTime, updateTime)

        self.Commit()

        return data[0]

    #-----------------------------------------------------------------------------------------------
    def Unanalyzed(self, detectedBy):
        """ report the current number of unanalyzed violations reported by detectedBy """

        s = """
        select count(*) from violations
        where detectedBy = ?
        and reviewDate is NULL
        """
        self.Execute( s, detectedBy)
        data = self.GetOne()

        return data[0]

    #-----------------------------------------------------------------------------------------------
    def Export(self, fn):
        """ Export the Db to a Csv file
        """

        s = """
        select filename,function,severity,violationId,description,details,lineNumber,
               detectedBy,firstReport,lastReport,status,analysis,who,reviewDate
               from violations
        """
        q = self.Query(s)

        f = open(fn, 'w', newline='')
        fcsv = csv.writer( f)

        fcsv.writerow( q.fields)
        for i in q:
            fcsv.writerow(i.data)

        f.close()

#===================================================================================================
if __name__ == '__main__':
    import ProjFile as PF

    if True:
        mainPfName = r'L:/FAST II/control processor/CodeReview/G4master.crp'
        mergePfName = r'C:/Users/P916214/Documents/Knowlogic/CodeReviewProj/FAST/G4.crp'

        mainPf = PF.ProjectFile(mainPfName)
        mergePf = PF.ProjectFile(mergePfName)

        mainDb = ViolationDb( mainPf.paths[PF.ePathProject])
        mergeDb = ViolationDb( mergePf.paths[PF.ePathProject])

        s = 'select count(*) from violations'
        d0 = mainDb.GetOne(s)
        d1 = mergeDb.GetOne(s)
        mainDb.Merge( mergeDb.dbName)

        mainDb.ShowMergeStats()
    else:
        pfName = r'C:\Users\P916214\Documents\Knowlogic\CodeReviewProj\FAST\G4.crp'
        mainPf = PF.ProjectFile(pfName)
        mainDb = ViolationDb( mainPf.paths[PF.ePathProject])

        mainDb.Export()
