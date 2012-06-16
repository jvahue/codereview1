"""
Violation DB
This file implements the Violation DB.  Any violation detected by any tool is reported here for
analysis.  The analysis performed can be recorded to identify who did it, when they did it and what
their analysis was.
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import os
import re

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
from utils.DB.database import Query
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

    #-----------------------------------------------------------------------------------------------
    def Open( self):
        self.Connect( self.dbName)

    #-----------------------------------------------------------------------------------------------
    def Insert( self, filename, function, severity, violationId, desc, details, line, detectedBy, updateTime):
        """ Insert a violation into the DB.
            If entry exists
                update lineNumber and description
                copy analysis if it exists
            else
                insert new row
        """
        function = function.strip()
        if function == '':
            function = 'N/A'

        details = details.strip()
        if details == '':
            details = 'N/A'
        else:
            # remove space to eliminate diffs
            detail0 = details.replace('  ', ' ')
            while detail0 != details:
                details = detail0
                detail0 = details.replace('  ',' ')

        # debug hook
        if filename==r'application\User.c' and function=='User_ExtractIndex' and severity=='Warning'and violationId =='613':
            pass

        # determine if this violation already exists in the DB
        s = """
            select description, details, lineNumber, detectedBy, lastReport
            from Violations where
            filename=?
            and function=?
            and severity=?
            and violationId=?
            and detectedBy=?
            and details=?
            and lastReport != ?
            """

        d = ( filename,function,severity,violationId,detectedBy,details,updateTime)
        if self.Execute( s, d) != 1:
            self.insertSelErr += 1
        data0 = Query(s, self, self.GetAll())

        isInsert = True
        if len(data0) > 0:
            descriptionRe = re.compile(self.GetDescriptionRe( desc))
            # pre-filter data set for our description
            # having us do this (vs. the DB with like) speeds thing s up a lot
            data = [i for i in data0 if descriptionRe.search(i.description)]

            if len(data) > 0:
                primary = ()
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
                        lineMatch = int(line) == i.lineNumber
                        descMatch = desc == i.description
                        # give preference to a lineNumber/desc match, then first in/first out
                        if primary == () or (matchLineNumber and lineMatch) or (not matchLineNumber and descMatch):
                            matchedItem = i
                            primary = (filename,function,severity,violationId,i.description,i.details,i.lineNumber)
                        isInsert = False
        else:
            pass

        if isInsert:
            d = (filename, function, severity, violationId, desc, details, line, detectedBy,updateTime,updateTime)
            s = """
                insert into Violations
                (filename,function,severity,violationId,description,details,lineNumber,detectedBy,firstReport,lastReport)
                values (%s)
                """ % ','.join('?'*len(d))
            if self.Execute( s, d) != 1:
                self.insertInErr += 1
            else:
                self.insertNew += 1
        else:
            updateItems = (updateTime, desc, details, line)
            s = """
                update Violations set lastReport=?, description=?, details=?, lineNUmber=? where
                filename=?
                and function=?
                and severity=?
                and violationID=?
                and description=?
                and details=?
                and lineNumber=?
                """
            if self.Execute( s, updateItems + primary) != 1:
                self.insertUpErr += 1
            else:
                self.insertUpdate += 1

    #-----------------------------------------------------------------------------------------------
    def GetDescriptionRe( self, desc, sql=False):
        """ Turn all line number referneces into a regex search
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
        self.Execute( s, (updateTime,))
        data = self.GetOne()

        # mark them as not being reported anymore
        s = """ update violations set
                status=?, reviewDate=?
                where lastReport != ?
                and detectedBy = '%s'
                and reviewDate is Null
            """ % (detectedBy)
        params = (eNotReported, updateTime, updateTime)
        self.Execute( s, params)

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
        self.Execute( s, (detectedBy,))
        data = self.GetOne()

        return data[0]
