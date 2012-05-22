"""
This file implements the specifics of a ODBC DB connection
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import os
import sys
import traceback

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------
import odbc

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
from utils.DB import database

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------

class DB_ODBC( database.DB):
    """ Quick class to encapsulate DB access """
    def __init__( self):
        database.DB.__init__( self)

    #------------------------------------------------------------------------------------------
    def Connect( self, connectionString):
        """ Connect to an ODBC database.  The user should know the connection string format
        MS Access: r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)}; Dbq=%s;" % filePath
        MS SQL: "DRIVER={SQL Server};SERVER=%s;UID=%s;PWD=%s;DATABASE=%s" % (server, UID,
                                                                             password, dbname)
        """
        try:
            print(connectionString)
            self.conn = odbc.odbc( connectionString)
            self._GetCursor()
        except:
            print("Connect: Unexpected error:\n", sys.exc_info())
            traceback.print_exc()
            self.conn =  None

#----------------------------------------------------------------------------------------------
class DB_Access( DB_ODBC):
    def __init__(self):
        DB_ODBC.__init__( self)

    #------------------------------------------------------------------------------------------
    def Connect( self, fileName):
        ext = os.path.splitext( fileName)[1]
        #conn = r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)}; Dbq=%s;" % fileName
        conn = r"DRIVER={Microsoft Access Driver (*%s)}; Dbq=%s;" % (ext,fileName)
        DB_ODBC.Connect( self, conn)

#----------------------------------------------------------------------------------------------
class DB_MS_SQL( DB_ODBC):
    def __init__(self):
        DB_ODBC.__init__( self)

    #------------------------------------------------------------------------------------------
    def Connect( self, server, UID, password, dbname):
        conn = "DRIVER={SQL Server};SERVER=%s;UID=%s;PWD=%s;DATABASE=%s" % (server, UID,
                                                                            password, dbname)
        DB_ODBC.Connect( self, conn)


