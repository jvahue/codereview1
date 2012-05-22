"""
This file handles loading PC-Lint issues into the DB
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import csv

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
eLintFields = 6

#---------------------------------------------------------------------------------------------------
# Classes / Functions
#---------------------------------------------------------------------------------------------------
class LntOutput:
    def __init__( self, fn=''):
        self.Reset( fn)

    def Reset(self, fn):
        self.isValid = False
        self.hdr = ''
        self.rawData = []
        self.reducedData = []
        self.duplicates = []
        self.matchData = []
        self.possibleMatch = []
        self.unmatched = []
        self.fn = fn
        if fn:
            self.fn = fn
            self.Read()

    def Read(self):
        f = open( self.fn, 'rb')
        csvf = csv.reader( f)
        self.hdr = csvf.next()
        # validate the contents
        self.isValid = True
        for i in csvf:
            if len(i) == eLintFields+1:
                self.rawData.append(i[1:]) # remove count field
            else:
                self.isValid = False
                self.rawData = []
                break
        f.close()

    def RemoveDuplicate(self):
        for i in self.rawData:
            if i not in self.reducedData:
                self.reducedData.append(i)
            else:
                self.duplicates.append(i)

    def InsertDb(self, data):
        """ CSV => [filename,function,line,severity,violationId,errText]
             DB => [filename,line,function,severity,detectedBy,violationId,errText]
        """
        print 'Inserting %d rows' % (len(data))
        counter = 0
        db = database.DB('__DEFAULT_DB__')
        for filename,function,line,severity,violationId,errText in data:
            s = """insert into KsCrLnt (filename,line,function,severity,detectedBy,violationId,errText)
                   values ('%s',%s,'%s','%s','%s','%s','%s')
                """ % (filename,line,function,severity,'Lint',violationId,errText)
            data = database.Query( s, db)
            counter += 1
            if (counter % 100) == 0:
                print counter

    def MatchDb(self):
        pass

csvf = r'C:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\Pc-Lint\results\all_1.csv'

lo = LntOutput( csvf)
print 'raw', len(lo.rawData)

lo.RemoveDuplicate()
print 'reduced', len(lo.reducedData)

lo.InsertDb( lo.reducedData)