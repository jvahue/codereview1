"""
This file implements the specifics of a SQL Lite DB connection
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import sqlite3
import sys
import traceback

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

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
class DB_SQLite( database.DB):
    """ Quick class to encapsulate DB access """
    def __init__( self):
        database.DB.__init__( self)

    #------------------------------------------------------------------------------------------
    def Close( self):
        if self.conn:
            self.conn.commit()

        database.DB.Close( self)

    #------------------------------------------------------------------------------------------
    def Connect( self, connectionString):
        """ Create a Sqlite3 connection.  The connection string is just the path to the DB
        """
        try:
            self.conn = sqlite3.connect(connectionString)
            self._GetCursor()
        except:
            print("Connect: Unexpected error:\n", sys.exc_info())
            traceback.print_exc()
            self.conn =  None

    #------------------------------------------------------------------------------------------
    def Commit( self):
        self.conn.commit()

