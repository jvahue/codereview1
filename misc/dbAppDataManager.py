#--------------------------------------------------------------------------
# dbAppDataManager.py
# Data Manager module of the Knowlogic Test Results Database Application
#
# This file defines the dataManager class and contains all of the main data
# management functions for the Test Results application. All file and data
# manipulation related to the application is done here. A dataManager object
# is created by the main application to handle any database connect, open,
# commit, table inserts and selects etc..  Database functionality should be
# kept strictly to this file in order to minimize effort in the event of a
# change in database interface.
#
#--------------------------------------------------------------------------

#--------------------------------------------------------------------------
# Python imports
#--------------------------------------------------------------------------
import sys
import os
import sqlite3
import csv    # trace.csv created by TraceData.py contains test result data


#--------------------------------------------------------------------------
# Third Party imports
#--------------------------------------------------------------------------

#--------------------------------------------------------------------------
# Knowlogic Module imports
#--------------------------------------------------------------------------
import database
import TraceData

#--------------------------------------------------------------------------
#  Functions
#--------------------------------------------------------------------------

#--TBD-- Should open and close be separate functions? Right now done in
#        DataManager init()

#def openTestResultsDB():
  # Initialize conn variable to None to avoid problems if we are unable to
  # create a connection to the database.
  #conn = None
  # Create connection object passing name of local file to storing database
  #conn = sqlite3.connect('knowlogicTestDB.db')

#def closeTestResultsDB():
    #if conn:
      #conn.close()

#--------------------------------------------------------------------------
# Class dataManager
#--------------------------------------------------------------------------
class dataManager:
    def __init__(self):
        self.db = r'knowlogicTestDB.db'
        #self.testResultsDir = r"C:" "\\"
        self.testResultsDir = r"."
        self.testResultData = []


        #--------------------------------------------------------------------------
        # Establish a DataBase connection, conn, and get a cursor object, curs, for
        # traversing the records.
        #--------------------------------------------------------------------------

        # Initialize conn variable to None to avoid problems if we are unable to
        # create a connection to the database.

        self.conn = None
        self.db_filename = os.path.join(self.testResultsDir, self.db)
        self.db_filename = os.path.normpath(self.db_filename)

        self.db_is_new = not os.path.exists(self.db_filename)


        # Create connection object passing db_filename for storing database

        #self.conn = sqlite3.connect(self.db_filename)
        self.conn = database.DB()
        self.db = self.conn
        #self.db.Reset( self.conn)

        # By using the with keyword for our connection, the Python interpreter
        # automatically releases the resources and provides error handling.

        #with self.conn:

          # Create a cursor for submitting SQL statements to the database server

        self.curs = self.conn.c #ursor()

        if self.db_is_new:
            print('db %s is new' % self.db_filename)

            # Build a CREATE TABLE SQL statement and execute it
            tblcmd = 'CREATE TABLE if not exists testResults(id INTEGER PRIMARY KEY ASC AUTOINCREMENT, tpi TEXT, type TEXT, result TEXT, xfi TEXT, script TEXT, srs TEXT, gse TEXT, log TEXT)'
            self.db.Execute(tblcmd)
            #self.curs.execute(tblcmd)

            # For now, call dmDbLoad here.
            #  It will create and read a csv file and insert into the database
            self.dmDbLoad("scriptName", r'G:\FAST v2.0\FASTTesting\DBApp\trace', "wid1", 5)

        else:
            print('db %s exists' % self.db_filename)

    #--------------------------------------------------------------------------
    # Function:
    #   dmDbLoad()
    # Parameters:
    #   scriptName, pathToScan, stationId, executionDuration)
    # Description:
    #   This call should be made at the completion of a test script.
    #   The purpose of this function is to run the tracedata.py program to
    #   produce the trace.csv file and then to use the trace.csv file
    #   to populate the testResults database.
    #
    #   For each entry in the trace.csv file containing the following data, a
    #   row is created in the testResults table of the database:
    #
    #   tpi - test point identifier
    #   type
    #   result - PASS, FAIL, or FAILOK
    #   xfi
    #   script
    #   srs
    #   gse
    #   log
    #
    #--------------------------------------------------------------------------
    def dmDbLoad(self, scriptName, pathToScan, stationId, executionDuration):

        # Run the tracedata.py program in the pathToScan passed in
        lds = TraceData.LogDirScanner(pathToScan)
        lds.Process()

        traceFileName = r'trace.csv'
        fName = os.path.join(pathToScan, traceFileName)

        print("Ready to get Test Results from %s" % fName)
        print("Inserting into %s database" % self.db_filename)
        reader = csv.reader(open(fName, 'rb'))
        try:
            for row in reader:
                print(row)
                # Add a row to the table
                #self.db.Execute("INSERT INTO testResults VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?)", row)
                self.db.c.execute("INSERT INTO testResults VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?)", row)
                #self.curs.execute("INSERT INTO testResults VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?)", row)

        except csv.Error as e:
            sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))

        self.conn.Commit()

    #--------------------------------------------------------------------------
    # Function:
    #   dmInsertTestResults()
    # Parameters:
    #   None
    # Description:
    #   The purpose of this function is to retrieve data from the trace.csv file
    #   created by TraceData.py and to update the test results database with the
    #   data retrieved.
    #
    #   For each entry in the trace.csv file containing the following data, a
    #   row is created in the testResults table of the database:
    #
    #   tpi - test point identifier
    #   type
    #   result - PASS, FAIL, or FAILOK
    #   xfi
    #   script
    #   srs
    #   gse
    #   log
    #
    #   TBD future values to add?
    #   workstationId - workstation identifier 1,2,3 or 4
    #   dateTime - timestamp (19 chars rtnd by datetime? YYYY-MM-DD HH:MM:SS)
    #
    #--------------------------------------------------------------------------
    def dmInsertTestResults(self, csvRootDir):

        traceFileName = r'trace.csv'
        fName = os.path.join(csvRootDir, traceFileName)
        print("Ready to get Test Results from %s" % fName)
        print("Inserting into %s database" % self.db_filename)
        reader = csv.reader(open(fName, 'rb'))
        try:
             for row in reader:
                print(row)
                # Add a row to the table
                #self.curs.execute("INSERT INTO testResults VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?)", row)
                self.db.Execute("INSERT INTO testResults VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?)", row)

        except csv.Error as e:
            sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))

        self.conn.Commit()

    #--------------------------------------------------------------------------
    # Function:
    #   dmExtractTestResults()
    # Parameters:
    #   None
    # Description:
    #   The purpose of this function is to retrieve data from the
    #   knowlogicTestDB.db database
    #
    #   For each row in the testResults table of the database, extract the data:
    #
    #   tpi - test point identifier
    #   type
    #   result - PASS, FAIL, or FAILOK
    #   xfi
    #   script
    #   srs
    #   gse
    #   log
    #
    #--------------------------------------------------------------------------
    def dmExtractTestResults(self):
        print("Ready to extract Test Results")

        # Select all rows from testResults table

        #self.curs.execute('SELECT * from testResults')
        self.db.Execute('SELECT * from testResults')
        print('Here is all the data in the database :')
        self.testResultData = self.curs.fetchall()
        for row in self.testResultData:
            print(row)


    #--------------------------------------------------------------------------
    # Function:
    #   dmMergeTestResultData()
    # Parameters:
    #   workstationId1 - workstation identifier 1,2,3 or 4
    #   workstationId2 - workstation identifier 1,2,3 or 4
    # Description:
    #   The purpose of this function is to merge the data testResult data in
    #   the databases on two workstations passed in.
    #
    #--------------------------------------------------------------------------
    #def dmMergeTestResultData():



