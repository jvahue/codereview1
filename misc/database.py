#==============================================================================================
#
# Descritpion: Database Wrapper functions
#
#==============================================================================================

import odbc
import os
import re
import socket
import sys
import time
import traceback
import util
import sqlite3
_debug = False
_askDBGagain = True
_debugQueryTime = 0

#----------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------
class ResultRow:
    def __init__( self, fields, data):
        self.data = data
        self.fields = fields
        try:
            self.length = len( data)
        except TypeError:
            self.length = 0
        self.index = 0

    #------------------------------------------------------------------------------------------
    def __str__( self):
        return str( self.data)

    #------------------------------------------------------------------------------------------
    def __repr__( self):
        return str( self.data)

    #------------------------------------------------------------------------------------------
    def __eq__( self, other):
        if isinstance( other, ResultRow):
            return self.data == other.data
        else:
            return self.data == other

    #------------------------------------------------------------------------------------------
    def __len__( self):
        return self.length

    #------------------------------------------------------------------------------------------
    def __getitem__( self, key):
        if type(key) == slice:
            return self.data[key.start:key.stop:key.step]
        elif abs(key) <= self.length:
            return self.data[key]
        else:
            raise IndexError

    #------------------------------------------------------------------------------------------
    def __getattr__( self, name):
        """ when only one field is requested from the query self.fields = [] so we just return
            the atomic value fetched
        """
        if self.data:
            if name in self.fields:
                x = self.fields.index(name)
                return self.data[x]
            elif self.fields == []:
                return self.data
            else:
                raise AttributeError
        else:
            return None

    #------------------------------------------------------------------------------------------
    def __iter__(self):
        """ Initialize the ieterator """
        self.index = 0
        return self

    #------------------------------------------------------------------------------------------
    def __next__( self):
        """ Get the next row form the data set """
        if self.index < self.length:
            rv = self.data[ self.index]
            self.index += 1
            return rv
        else:
            raise StopIteration

#----------------------------------------------------------------------------------------------
class DB:
    """ Quick class to encapsulate DB access """
    def __init__( self, DBparam = None, special = None):
        self.DBparam = DBparam
        self.special = special
        self.Reset()

    def Reset( self, forceDbUse=None):
        tries = 0
        while tries < 6:
            if forceDbUse is None:
                self.db = GetDB( self.DBparam, self.special)
            else:
                self.db = forceDbUse
            if self.db:
                self.c  = GetCursor( self.db)
                break
            else:
                time.sleep(10)
                tries += 1
                if (_debug): print('DB connection retry in 10 seconds')
                self.c = None

    #------------------------------------------------------------------------------------------
    def Execute( self, sql):
        """ Execute a query, attempt to reconnect to the DB if the connection is lost """
        if self.c:
            if (_debug): print("Execute: ", sql)
            while 1:
                try:
                    self.c.execute( sql)
                    return 1
                except :
                    if _debug:
                        print(traceback.print_exc())
                        print()
                        print(sql)
                    return 0
        else:
            return None

    #------------------------------------------------------------------------------------------
    def GetAll( self, sql = None):
        """ Execute a query if provided and return the entire set """
        start = time.clock()
        if self.c:
            if sql: self.Execute( sql)
            data = GetAll( self.c)
            self.queryTime = time.clock() - start
        else:
            data = None
            self.queryTime = -1
        return data

    #------------------------------------------------------------------------------------------
    def GetOne( self, sql = None):
        """ Execute a query if provided and return one from the cursor
            repeat with no sql to work through the cursor
        """
        start = time.clock()
        if sql: self.Execute( sql)
        data = GetOne( self.c)
        self.queryTime = time.clock() - start
        return data

    #------------------------------------------------------------------------------------------
    def __del__( self):
        if self.db:
            Close( self.db)

    #------------------------------------------------------------------------------------------
    def MakeTupleStr( self, l):
        # create a str tuple representation usable by a DB query
        if len(l) == 0:
            t = '(NULL)'
        else:
            t = str(tuple(l))
            if len(l) == 1:
                t = t.replace(',','')

        return t

    #------------------------------------------------------------------------------------------
    def Close( self):
        self.db.Close()

    #------------------------------------------------------------------------------------------
    def Commit( self):
        self.db.commit()

#----------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------
class Query:
    """ A query Iterator object, allows a result set to be iterated over easily
        Additionally this object dynamically generates functions based on the selected
        fields in the query so you can access them by name i.e.,

        sql = 'select a,b from table'
        q = Query(sql)
        for i in q:
            a = i.a
            b = i.b

        when the fields are qualified such as
            'T.fieldX' the access name becomes fieldX
            'name = T.fieldX' the access name becomes name
            'T.field as name' becomes name
    """
    def __init__( self, query, db = None, data = None):
        """ Initalize a query object, needs a query """
        self.index = 0
        self.dataSet = ()
        self.data = None
        self.fields = []
        self.query = query

        if data == None:
            if db:
                if type( db) == str:
                    dba = DB(db)
                else:
                    dba = db
            else:
                dba = DB('__DEFAULT_DB__')

            # get the data and query time
            start = time.clock()
            self.dataSet = dba.GetAll( query)
            self.queryTime = time.clock() - start
            del dba
        else:
            self.dataSet = data
        self.reset( query, self.dataSet)

    #------------------------------------------------------------------------------------------
    def reset( self, query, data):
        self.index = 0
        self.dataSet = data
        self.length = len( self.dataSet)

        if self.length > 0:
            self.data = self.dataSet[0]
            if type(self.data) in (list, tuple):
                if len(self.data) == 1:
                    # flatten it into a simple list
                    self.dataSet = [i for i, in self.dataSet]
                    self.data = self.dataSet[0]
                    self.fields = []
                else:
                    # properties creation
                    self.Properties( query)
            else:
                self.fields = []
        else:
            self.data = None
            self.fields = []

    #------------------------------------------------------------------------------------------
    def __len__( self):
        """ return the length of the data set """
        return self.length

    #------------------------------------------------------------------------------------------
    def __getitem__( self, key):
        """ return the selected item/slice
            for a slice return a new Query object with the specified slice
        """
        if type(key) == slice:
            return Query( self.query, data=self.dataSet[key.start:key.stop:key.step])
        elif abs(key) <= self.length:
            self.data = ResultRow( self.fields, self.dataSet[key])
            return self.data
        else:
            raise IndexError

    #------------------------------------------------------------------------------------------
    def __contains__( self, item):
        """ see if what we want is in the data set """
        return item in self.dataSet

    #------------------------------------------------------------------------------------------
    def __iter__(self):
        """ Initialize the ieterator """
        self.index = 0
        if self.length > 0:
            self.data = self.dataSet[self.index]
        return self

    #------------------------------------------------------------------------------------------
    def __next__( self):
        """ Get the next row form the data set """
        if self.index < self.length:
            self.data = ResultRow( self.fields, self.dataSet[self.index])
            self.index += 1
            return self.data
        else:
            raise StopIteration

    #------------------------------------------------------------------------------------------
    def __bool__( self):
        """ Check if the query returned anything eg.
            d = Query(s)
            if d:
                ...
        """
        return (self.length > 0)

    #------------------------------------------------------------------------------------------
    def __getattr__( self, name):
        """ This function provides the capability to fetch data values by the DB field names
            When only one field is requested in the query self.fields = [] and the tuples
            returned are flatten (see reset) so we just return the atomic value fetched which
            is in self.data
        """
        if self.dataSet:
            if name in self.fields:
                x = self.fields.index(name)
                return self.data[x]
            elif self.fields == []:
                return self.data
            else:
                raise AttributeError
        else:
            return None

    #------------------------------------------------------------------------------------------
    def reverse( self):
        """ reverse the order of the dataSet """
        if self.length > 0:
            self.dataSet.reverse()
            self.index = 0
            self.data = self.dataSet[0]

    #------------------------------------------------------------------------------------------
    def MakeTupleStr( self, l):
        """ create a str tuple representation usable by a DB query """
        if len(l) == 0:
            t = '(NULL)'
        else:
            t = str(tuple(l))
            if len(l) == 1:
                t = t.replace(',','')

        return t

    #------------------------------------------------------------------------------------------
    def Properties( self, query):
        """ build field reference names from the query string for __getattr__ """
        selAt = query.lower().find('select')
        newFields = []
        if selAt != -1:
            selAt += len('select')
            fromAt = query.lower().find('from')
            fields = query[selAt:fromAt]
            fields = fields.replace('\n', ' ')
            # remove SQL functions
            fields = self.SQLfields( fields)
            fields = fields.split(',')
            fields = [i.strip() for i in fields]

            # process select column syntax
            for field in fields:
                # change N = T.F to N
                eq = field.find('=')
                if eq != -1:
                    field = field[:eq].strip()
                else:
                    # change T.F as N to N
                    asX = field.find(' as ')
                    if asX != -1:
                        field = field[asX+4:].strip()
                    else:
                        # change table.field to field
                        per = field.find('.')
                        if per != -1:
                            field = field[per+1:].strip()
                newFields.append( field)
        self.fields = newFields

    #------------------------------------------------------------------------------------------
    def SQLfields( self, fields):
        """ return a string with SQL functions removed by parameter count
        """
        castRE = re.compile( r'cast *\(.+?\)', re.IGNORECASE)
        convertRE = re.compile( r'convert *\(.+?\)', re.IGNORECASE)
        isnullRE = re.compile( r'isnull *\(.+?\)', re.IGNORECASE)
        fieldRE = { castRE:0, convertRE:1, isnullRE:0}
        for theRE in fieldRE:
            paramNum = fieldRE[theRE]
            fields = self.FieldSearch( fields, theRE, paramNum)

        #remove single param functions
        single = ('max', 'min', 'sum', 'ceiling', 'floor')
        for i in single:
            reFmt = re.compile( r'%s *\(.+?\)' % i, re.IGNORECASE)
            fields = self.FieldSearch( fields, theRE, 0)

        removeList = ('distinct', '(', ')')
        for i in removeList:
            fields = fields.replace( i, '')
        return fields

    #------------------------------------------------------------------------------------------
    def FieldSearch( self, fields, theRE, paramNum):
        matches = theRE.findall( fields)
        for theMatch in matches:
            replaceStr = self.GetExpression( theMatch, paramNum)
            fields = fields.replace( theMatch, replaceStr)
        return fields

    #------------------------------------------------------------------------------------------
    def GetExpression( self, aMatch, index):
        # remove before and after the parenthesis inclusive
        lp = aMatch.find('(')
        rp = aMatch.find(')')
        aMatch = aMatch[lp+1:rp]
        # split the string on ','
        a1Match = aMatch.split(',')
        if len(a1Match) == 1:
            # split on 'AS'
            a1Match = aMatch.lower().split(' as ')
        return a1Match[index]

#----------------------------------------------------------------------------------------------
def DBaccessStr():
    server = input('Enter the server name: ')
    UID = input('Enter the user ID: ')
    password = input('Enter the password: ')
    dbname = input('Enter the DB name: ')
    accessStr = "DRIVER={SQL Server};SERVER=%s;UID=%s;PWD=%s;DATABASE=%s" % (server, UID,
                                                                             password, dbname)

    return accessStr

#----------------------------------------------------------------------------------------------
def GetDB( DBparam = None, special = None):
    """ Get a DB connection
        DBparam == '__DEFAULT_DB__' provides connection to default DB based on the
                   host machine name.  This is really for the Live servers 'dbserv','webserv'
                   Any machine in Altair will default to the live backup 'Groundsoft_DBSERV'
        special == 'special' means that the special param will hold the login info for the
                   require DB
    """
    global _debug
    global _askDBGagain
    
    name = r'knowlogicTestDB.db'
    conn = sqlite3.connect(name)
    return conn


    #Open a DB connection, Check to see if we are running this on the live site
    host = socket.gethostname()
    if host == 'AE415730':
        p = r'H:\Knowlogic\Documents\Trace\TraceDB.mdb'
    elif host == 'Main':
        p = r'F:\Knowlogic\Documents\Trace\TraceDB.mdb'
    elif host == 'Jeff-Laptop':
        p = r'I:\Knowlogic\Documents\Trace\TraceDB.mdb'
    else:
        p = r'E:\Knowlogic\Documents\Trace\TraceDB.mdb'

    DBselect = 'DB'
    if DBselect.lower() == 'special':
        DBselect = 'DB'
        p = special

    # DB Choices
    DBchoices = {
      "DB": r"DRIVER={Microsoft Access Driver (*.mdb)}; Dbq=%s;" % p,
    }

    print('help')
    return None
    try:
        login = DBchoices[ DBselect]
        return odbc.odbc( login)
    except:
        print("GetDB: Unexpected error:\n", sys.exc_info())
        traceback.print_exc()
        return None

#----------------------------------------------------------------------------------------------
def Close( db):
    """ Close the DB connection """
    try:
        db.close()
        return 1
    except:
        print("Close: Unexpected error:\n", sys.exc_info())
        traceback.print_exc()
        return 0

#----------------------------------------------------------------------------------------------
def GetCursor( db):
    """ return a cursor for a database """
    try:
        return db.cursor()
    except:
        print("GetCursor: Unexpected error:\n", sys.exc_info())
        traceback.print_exc()
        return None

#----------------------------------------------------------------------------------------------
def GetDBC( DBparam = None, special = None):
    """ return a Db connection and a cursor"""
    db = GetDB( DBparam, special)
    c = GetCursor( db)
    return db, c

#----------------------------------------------------------------------------------------------
def Execute( cursor, sql):
    """ Execute a SQL statement against a specified cursor """
    try:
        if (_debug): print("Execute: ", sql)
        cursor.execute( sql)
        return 1
    except:
        if (_debug):
            print("Execute: Unexpected error:\n", sys.exc_info())
            traceback.print_exc()
        return 0

#----------------------------------------------------------------------------------------------
def GetAll( c):
    """ return the cursor result set """
    global _debugQueryTime
    try:
        start = time.clock()
        allOfThem = c.fetchall()
        _debugQueryTime = time.clock() - start
        if allOfThem == None:
            allOfThem = []
        return allOfThem
    except:
        if (_debug):
            print("GetAll: Unexpected error:\n", sys.exc_info())
            traceback.print_exc()
        return []

#----------------------------------------------------------------------------------------------
def GetOne( c):
    """ return the top row of the cursor result set working through the set """
    global _debugQueryTime
    try:
        start = time.clock()
        theOne = c.fetchone()
        _debugQueryTime = time.clock() - start
        if theOne == None:
            theOne = ()
        return theOne
    except:
        if (_debug):
            print("GetOne: Unexpected error:\n", sys.exc_info())
            traceback.print_exc()
        return ()

#----------------------------------------------------------------------------------------------
def DebugState( state):
    global _debug
    if state:
        _debug = True
    else:
        _debug = False

#----------------------------------------------------------------------------------------------
def GS_DBlist():
    """ Create a file with table information """
    db = DB('__DEFAULT_DB__')
    tables = AllTableList( db)

    f = file( 'DB.dat', 'w')

    for i, in tables:
        print('Process: %s' % i)
        str = '------------------ %s' % (i)
        f.write( str + '\n')
        ListTable( i, db, f)

    f.write( '%d Tables\n' % (len(tables)))
    f.close()

#----------------------------------------------------------------------------------------------
def AllTableList(db):
    """ Returns a list of every user table in the database """
    if not db:
        db = database.DB('__DEFAULT_DB__')
    all = db.GetAll("SELECT name FROM sysobjects WHERE xtype='U' ORDER BY name")
    return all

#----------------------------------------------------------------------------------------------
def ListTable( table, db, f):
    """ Get Column info """
    info = db.GetAll( "sp_columns @table_name='%s'" % table)
    pk = db.GetAll("sp_pkeys @table_name='%s'" % table) # primary key info
    # strip pk column names
    pk = [i[3] for i in pk]
    for i in info:
        str = 'Column[%32s ] Type[%15s ] Nullable[%3s] Primary[ %3s ]' % (
               i[3], i[5], i[10] and 'Yes' or ' No', i[3] in pk and 'Yes' or ' No')
        f.write(str + '\n')

#----------------------------------------------------------------------------------------------
def TestDBexecuteRetry():
    db = DB('__DEFAULT_DB__')
    for i in range(1000):
        s = 'select count(*) from gs_install'
        print('%3d' % i, time.asctime(time.localtime()), db.GetAll(s))
        time.sleep(5)

#----------------------------------------------------------------------------------------------
if __name__ == '__main__':
    GS_DBlist()
