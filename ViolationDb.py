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
            os.makedirs( self.dbPath)

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

        if filename==r'drivers\arinc429.c' and function=='Arinc429DrvSetIMR1_2' and severity=='Info'and violationId =='845':
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
        data = Query(s, self, self.GetAll())

        isInsert = True
        primary = ()
        if len(data) > 0:
            # scan through the description and check for matches
            #   convert line numbers to regex for comparison
            descriptionRe = re.compile(self.GetDescriptionRe( desc))
            for i in data:
                m = descriptionRe.search(i.description)
                if m:
                    # give preference to a lineNumber match, then first in/first out
                    if primary == () or int(line) == i.lineNumber:
                        matchedItem = i
                        primary = (filename,function,severity,violationId,i.description,i.details,i.lineNumber)
                    isInsert = False

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
            # here we update the row with only new info or we get a primary key violation reported
            updateItemNames = ['lastReport']
            updateItems = [updateTime]

            # check description, details and lineNumber
            if desc != matchedItem.description:
                updateItemNames.append( 'description')
                updateItems.append( desc)
            if details != matchedItem.details:
                updateItemNames.append( 'details')
                updateItems.append( details)
            if int(line) != matchedItem.lineNumber:
                updateItemNames.append( 'lineNumber')
                updateItems.append( line)

            # make the update str
            updateStr = ['%s=?' % i for i in updateItemNames]
            updateStr = ', '.join( updateStr)
            updateItems = tuple(updateItems)

            s = """
                update Violations set %s where
                filename=?
                and function=?
                and severity=?
                and violationID=?
                and description=?
                and details=?
                and lineNumber=?
                """ % updateStr
            if self.Execute( s, updateItems + primary) != 1:
                self.insertUpErr += 1
            else:
                self.insertUpdate += 1

    #-----------------------------------------------------------------------------------------------
    def GetDescriptionRe( self, desc):
        """ Turn all line number referneces into a regex search
        Ignoring return value of function 'foo(void)' (compare with line 163, file xyz.h)
        Storage class of symbol 'foo(void *)' assumed static (line 150)
        """
        lineRe = re.compile(r'[Ll]ine[ \t]+([0-9]+)')
        m = lineRe.findall( desc)

        # escape special regex chars in the description
        # the '\' must be first so it only replaces itself when it in the original string
        for c in r'\.^$*+?{}[]|()':
            desc = desc.replace(c, r'\%s' % c)

        if m:
            # now put the number regex in
            for i in m:
                desc = desc.replace(i, '[0-9]+')

        return desc

