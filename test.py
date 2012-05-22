"""
Code review Main
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
from .utils.DB.database import Query
from .utils.DB.odbc.database import DB_Access
from .utils.DB.sqlLite.database import DB_SQLite

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------

odb = DB_Access()
odb.Connect( r'db1.mdb')

sl3 = DB_SQLite()
sl3.Connect(r'test.db')
sl3.Execute('CREATE TABLE if not exists test(date text, start TEXT, end TEXT, cust TEXT, proj TEXT, class TEXT, type TEXT, duration TEXT)')
sl3.Commit()

data = Query( "select date, start,end, cust, proj, class, 'work Type' as type, dur from 2012 where proj = 'AT4'", odb)

for i in data:
    print('odb', i)
    data = i.data
    sl3.Execute("insert into test VALUES(?, ?, ?, ?, ?, ?, ?, ?)", data)

sl3.Commit()


data = Query( "select date, start,end, cust, proj, class, type, duration from test where proj = 'AT4'", sl3)


for i in data:
    print('sl3', i)
