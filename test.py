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
from utils.DB.database import Query
from utils.DB.sqlLite.database import DB_SQLite

from tools.pcLint import PcLint

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
def TestDb():
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

def TestPcLint():
    projRoot = r'D:\Knowlogic\zzzCodereviewPROJ'
    srcCodeRoot = r'D:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP'
    options = {}
    options['sizeOptions'] = '-si4 -sp4'

    incStr = """
    -iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\application
    -iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\drivers
    -iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\drivers\hwdef
    -iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\system
    -iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\test
    """
    includes = [i.strip() for i in incStr.split('\n') if i.strip() ]
    options['includes'] = includes

    options['defines'] = '-D__m68k'

    # get the srcFiles only take .c for testing
    srcFiles = []
    for dirPath, dirs, fileNames in os.walk( srcCodeRoot):
        for f in fileNames:
            ffn = os.path.join( dirPath, f)
            if os.path.isfile(ffn) and os.path.splitext( f) == '.c':
                srcFiles.append( ffn)

    pcls = PcLintSetup( projRoot)
    pcls.CreateProject( srcFiles, options)



def Test():
    sel = input( 'Run All=1, Load=0: ')
    if sel == '1':
        PcLint.TestCreate()
        PcLint.TestRun()
    else:
        PcLint.Load()

Test()