"""
This file provides base class DB objects:

1. DB - a DB object, connections, cursors, execute, fetchall, fetch, commit, etc.
2. Query - an object for executing a query and allows query field name references for accessing
   data in the results
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import os
import re
import socket
import sys
import time
import traceback

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
from utils import util
from .ResultRow import ResultRow

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
_debug = False
_askDBGagain = True
_debugQueryTime = 0

eDbDebugOff = 0
eDbDebugErr = 1
eDbDebugAll = 2

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------
def MakeTupleStr( l):
    # create a str tuple representation usable by a DB query
    if len(l) == 0:
        t = '(NULL)'
    else:
        t = str(tuple(l))
        if len(l) == 1:
            t = t.replace(',','')

    return t

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------

#----------------------------------------------------------------------------------------------
class DB:
    """ Quick class to encapsulate DB access """
    def __init__( self):
        self.conn = None
        self.cursor = None
        self.queryValid = False
        self.debug = 0

    #------------------------------------------------------------------------------------------
    def __del__( self):
        if self.conn:
            self.Close()

    #------------------------------------------------------------------------------------------
    def Schema( self):
        """ return a dictionary of
            table => [(field1, attributes), (field2, attributes)]
            NOTE: all items are in lower case
        """
        raise NotImplemented

    #------------------------------------------------------------------------------------------
    def IsSqlReservedWord( self, word):
        return  word.lower() in sqlReservedWords

    #------------------------------------------------------------------------------------------
    def Close( self):
        try:
            self.conn.close()
            self.conn = None
            return 1
        except:
            if self.debug > eDbDebugOff:
                print("Close: Unexpected error:\n", sys.exc_info())
                traceback.print_exc()
            return 0

    #------------------------------------------------------------------------------------------
    def Commit( self):
        pass

    #------------------------------------------------------------------------------------------
    def Connect( self, connectionString):
        raise NotImplemented

    #------------------------------------------------------------------------------------------
    def Query( self, sql, *args):
        qr = None
        if self.Execute( sql, *args):
            data = self.GetAll()
            qr = Query( sql, self, data = data)
        return qr

    #------------------------------------------------------------------------------------------
    def Execute( self, sql, *args):
        """ Execute a query if we have a connection
        Params:
            sql: the query to execute
            *args: any args to supply to the query
        Returns:
            -1: if no connection available
             0: on sql failure
             1: on success
        """
        rv = -1
        self.queryValid = False

        if self.cursor is not None:
            if (self.debug > eDbDebugErr): print("Execute: ", sql)
            self.queryValid = True
            try:
                if args:
                    self.cursor.execute( sql, args)
                else:
                    self.cursor.execute( sql)
                rv = 1
            except :
                self.queryValid = False
                print(traceback.print_exc(file=sys.stdout))
                print('---------------')
                print(sql)
                if args:
                    for i in args:
                        print(i)
                rv = 0
        return rv

    #------------------------------------------------------------------------------------------
    def GetAll( self, sql = None):
        """ Execute a query if provided and return the entire result set
        Params:
            sql: an optional sql statement
        Returns:
            if a sql statement is provide the result set from that, otherwise any results
            pending from a previously performed sql execute
            if no connection returns None
        """
        start = time.clock()
        if self.cursor:
            if sql: self.Execute( sql)
            if self.queryValid:
                data = self._GetAll()
            else:
                data = None
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
        data = GetOne( self.cursor)
        self.queryTime = time.clock() - start
        return data

    #------------------------------------------------------------------------------------------
    # Utility Functions
    #------------------------------------------------------------------------------------------
    def DebugState( self, state):
        self.debug = state

    #----------------------------------------------------------------------------------------------
    def _GetCursor( self):
        """ return a cursor for a database """
        try:
            self.cursor = self.conn.cursor()
        except:
            if self.debug > eDbDebugOff:
                print("GetCursor: Unexpected error:\n", sys.exc_info())
                traceback.print_exc()
            self.cursor =  None

    #------------------------------------------------------------------------------------------
    def _GetAll( self):
        """ Get all results from a query
        Params: None
        Returns:
            a list of the result set on success
            an empty list [] otherwise
        """
        try:
            allOfThem =  self.cursor.fetchall()
            if allOfThem == None:
                allOfThem = []
            return allOfThem
        except:
            if (self.debug > eDbDebugOff):
                print("GetAll: Unexpected error:\n", sys.exc_info())
                traceback.print_exc()
            return []

    #------------------------------------------------------------------------------------------
    def _GetOne( self):
        """
        """
        try:
            theOne = self.cursor.fetchone()
            if theOne == None:
                theOne = ()
            return theOne
        except:
            if (self.debug  > eDbDebugOff):
                print("GetOne: Unexpected error:\n", sys.exc_info())
                traceback.print_exc()
            return ()


#----------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------
class Query:
    """ A query Iterator object, allows a result set to be iterated over easily. This object
        allows access to the select fields named in the query, by the names used in the query.
        e.g.,
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
    def __init__( self, query, db, data = None):
        """ Initialize a query object, needs a query
        params:
            query: the query to run, or the query that sourced the data
            db: a DB object to perform the query
            data: if we want to init the Query object with some predefined data
        """
        self.index = 0
        self.dataSet = ()
        self.data = None
        self.fields = []
        self.query = query

        if data == None:
            # get the data and query time
            start = time.clock()
            self.dataSet = db.GetAll( query)
            self.queryTime = time.clock() - start
        else:
            self.dataSet = data

        self.Reset( query, self.dataSet)

    #------------------------------------------------------------------------------------------
    def Reset( self, query, data):
        self.index = 0
        self.dataSet = data
        if data is not None:
            self.length = len( self.dataSet)
        else:
            self.length = 0

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

    #Open a DB connection, Check to see if we are running this on the live site
    host = socket.gethostname()
    #cwd = os.getcwd()
    p = r'C:\Knowlogic\tools\KsCrLnt\KsCrLnt.accdb'
    #if host == 'AE415730':
    #    p = r'H:\PWC\Knowlogic\Documents\Trace\TraceDB.mdb'
    #elif host == 'Main':
    #    p = r'..\TraceDB.mdb'
    #elif host == 'Jeff-Laptop':
    #    p = r'I:\PWC\Knowlogic\Documents\Trace\TraceDB.mdb'
    #else:
    #    p = r'E:\PWC\Knowlogic\Documents\Trace\TraceDB.mdb'

    DBselect = 'DB'
    if DBselect.lower() == 'special':
        DBselect = 'DB'
        p = special

    # DB Choices
    DBchoices = {
      "DB": r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)}; Dbq=%s;" % p,
    }

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


sqlReservedWords = ('absolute',
'action',
'add',
'after',
'all',
'allocate',
'alter',
'and',
'any',
'are',
'array',
'as',
'asc',
'asensitive',
'assertion',
'asymmetric',
'at',
'atomic',
'authorization',
'avg',
'before',
'begin',
'between',
'bigint',
'binary',
'bit',
'bit_length',
'blob',
'boolean',
'both',
'breadth',
'by',
'call',
'called',
'cascade',
'cascaded',
'case',
'cast',
'catalog',
'char',
'character',
'character_length',
'char_length',
'check',
'clob',
'close',
'coalesce',
'collate',
'collation',
'column',
'commit',
'condition',
'connect',
'connection',
'constraint',
'constraints',
'constructor',
'contains',
'continue',
'convert',
'corresponding',
'count',
'create',
'cross',
'cube',
'current',
'current_date',
'current_default_transform_group',
'current_path',
'current_role',
'current_time',
'current_timestamp',
'current_transform_group_for_type',
'current_user',
'cursor',
'cycle',
'data',
'date',
'day',
'deallocate',
'dec',
'decimal',
'declare',
'default',
'deferrable',
'deferred',
'delete',
'depth',
'deref',
'desc',
'describe',
'descriptor',
'deterministic',
'diagnostics',
'disconnect',
'distinct',
'do',
'domain',
'double',
'drop',
'dynamic',
'each',
'element',
'else',
'elseif',
'end',
'equals',
'escape',
'except',
'exception',
'exec',
'execute',
'exists',
'exit',
'external',
'extract',
'false',
'fetch',
'filter',
'first',
'float',
'for',
'foreign',
'found',
'free',
'from',
'full',
'function',
'general',
'get',
'global',
'go',
'goto',
'grant',
'group',
'grouping',
'handler',
'having',
'hold',
'hour',
'identity',
'if',
'immediate',
'in',
'indicator',
'initially',
'inner',
'inout',
'input',
'insensitive',
'insert',
'int',
'integer',
'intersect',
'interval',
'into',
'is',
'isolation',
'iterate',
'join',
'key',
'language',
'large',
'last',
'lateral',
'leading',
'leave',
'left',
'level',
'like',
'local',
'localtime',
'localtimestamp',
'locator',
'loop',
'lower',
'map',
'match',
'max',
'member',
'merge',
'method',
'min',
'minute',
'modifies',
'module',
'month',
'multiset',
'names',
'national',
'natural',
'nchar',
'nclob',
'new',
'next',
'no',
'none',
'not',
'null',
'nullif',
'numeric',
'object',
'octet_length',
'of',
'old',
'on',
'only',
'open',
'option',
'or',
'order',
'ordinality',
'out',
'outer',
'output',
'over',
'overlaps',
'pad',
'parameter',
'partial',
'partition',
'path',
'position',
'precision',
'prepare',
'preserve',
'primary',
'prior',
'privileges',
'procedure',
'public',
'range',
'read',
'reads',
'real',
'recursive',
'ref',
'references',
'referencing',
'relative',
'release',
'repeat',
'resignal',
'restrict',
'result',
'return',
'returns',
'revoke',
'right',
'role',
'rollback',
'rollup',
'routine',
'row',
'rows',
'savepoint',
'schema',
'scope',
'scroll',
'search',
'second',
'section',
'select',
'sensitive',
'session',
'session_user',
'set',
'sets',
'signal',
'similar',
'size',
'smallint',
'some',
'space',
'specific',
'specifictype',
'sql',
'sqlcode',
'sqlerror',
'sqlexception',
'sqlstate',
'sqlwarning',
'start',
'state',
'static',
'sthen',
'submultiset',
'substring',
'sum',
'symmetric',
'system',
'system_user',
'table',
'tablesample',
'temporary',
'then',
'time',
'timestamp',
'timezone_hour',
'timezone_minute',
'to',
'trailing',
'transaction',
'translate',
'translation',
'treat',
'trigger',
'trim',
'true',
'under',
'undo',
'union',
'unique',
'unknown',
'unnest',
'until',
'update',
'upper',
'usage',
'user',
'using',
'value',
'values',
'varchar',
'varying',
'view',
'when',
'whenever',
'where',
'while',
'window',
'with',
'within',
'without',
'work',
'write',
'year',
'zone',)

#----------------------------------------------------------------------------------------------
if __name__ == '__main__':
    GS_DBlist()
