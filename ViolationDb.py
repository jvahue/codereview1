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
                       'lineNumber integer',  # not primary as this will change over time
                       'detectedBy text',
                       'firstReport timestamp',
                       'lastReport timestamp',
                       'status text',
                       'analysis text',
                       'who text',
                       'reviewDate timestamp',
                       'primary key (filename,function,severity,violationId,description)',
                       )
            query  = 'CREATE TABLE if not exists Violations(%s)' % ','.join(fields)
            if self.Execute(query):
                self.Commit()

    #-----------------------------------------------------------------------------------------------
    def Open( self):
        self.Connect( self.dbName)

    #-----------------------------------------------------------------------------------------------
    def Insert( self, filename, function, severity, violationId, desc, line, detectedBy, updateTime):
        """ Insert a violation into the DB.
            If entry exists
                update lineNumber and description
                copy analysis if it exists
            else
                insert new row
        """

        if function.strip() == '':
            function = 'N/A'

        # determine if this violation already exists in the DB
        s = """
            select description, lineNumber, detectedBy, lastReport
            from Violations where
            filename=?
            and function=?
            and severity=?
            and violationId=?
            and detectedBy=?
            and lastReport != ?
            """
        d = ( filename,function,severity,violationId,detectedBy,updateTime)
        self.Execute( s, d)
        data = Query(s, self, self.GetAll())

        isInsert = True
        if len(data) > 0:
            # scan through the description and check for matches
            #   convert line numbers to regex for comparison
            descriptionRe = re.compile(self.GetDescriptionRe( desc))
            for i in data:
                m = descriptionRe.search(i.description)
                if m:
                    primary = (filename,function,severity,violationId,i.description)
                    isInsert = False
                    break

        if isInsert:
            s = """
                insert into Violations
                (firstReport,filename,function,severity,violationId,description,lineNumber,detectedBy,lastReport)
                values (?,?,?,?,?,?,?,?,?)
                """
            d = (updateTime,filename, function, severity, violationId, desc, line, detectedBy,updateTime)
            self.Execute( s, d)
        else:
            # here we update the row with (possibly) new info
            s = """
                update set description=?, line=?, lastReport=? where
                filename=?
                and function=?
                and severity=?
                and violationID=?
                and description=?
                """
            self.Execute( s, (desc, line, updateTime) + primary)

    #-----------------------------------------------------------------------------------------------
    def GetDescriptionRe( self, desc):
        """ Turn all line number referneces into a regex search
        Ignoring return value of function 'foo(void)' (compare with line 163, file xyz.h)
        Storage class of symbol 'foo(void *)' assumed static (line 150)
        """
        lineRe = re.compile(r'[Ll]ine[ \t]+([0-9]+)')
        m = lineRe.findall( desc)

        if m:
            # the '\' must be first so it only replaces itself when it in the original string
            for c in r'\.^$*+?{}[]|()':
                desc = desc.replace(c, r'\%s' % c)

            # now put the number regex in
            for i in m:
                desc = desc.replace(i, '[0-9]+')

        return desc

