"""
This file handles loading PC-Lint issues into the DB
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import csv
import datetime

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
eLintFields = 7

#---------------------------------------------------------------------------------------------------
# Classes / Functions
#---------------------------------------------------------------------------------------------------
class LintLoader:
    def __init__( self, fn, db):
        self.Reset( fn, db)

    #-----------------------------------------------------------------------------------------------
    def Reset(self, fn, db):
        self.isValid = False
        self.hdr = ''
        self.rawData = []
        self.reducedData = []
        self.duplicates = []
        self.matchData = []
        self.possibleMatch = []
        self.unmatched = []
        self.fn = fn
        self.db = db
        if fn:
            self.fn = fn
            self.Read()

    #-----------------------------------------------------------------------------------------------
    def Read(self):
        f = open( self.fn, 'r', newline='')
        csvf = csv.reader( f)
        self.hdr = csvf.__next__()
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

    #-----------------------------------------------------------------------------------------------
    def RemoveDuplicate(self):
        for i in self.rawData:
            if i not in self.reducedData:
                self.reducedData.append(i)
            elif i not in self.duplicates:
                self.duplicates.append(i)

    #-----------------------------------------------------------------------------------------------
    def InsertDb(self, data):
        """ CSV => [1,filename,function,line,severity,violationId,errText,details]
             DB => [filename,function,severity,violationId,errText,details,line,detectedBy]
        """
        self.updateTime = datetime.datetime.today()

        print( 'Processing %d rows' % (len(data)))
        counter = 0
        db = self.db
        for filename,func,line,severity,violationId,desc,details in data:
            db.Insert( filename,func,severity,violationId,desc,details,line,'PcLint',self.updateTime)
            counter += 1
            if (counter % 100) == 0:
                print( '%d\r' % counter),
        db.Commit()

        s = """
            select count(*) from violations where lastReport != ?
            """
        db.Execute( s, (self.updateTime,))
        data = db.GetOne()
        return data[0], self.updateTime

#===================================================================================================
if __name__ == '__main__':
    csvf = r'C:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\Pc-Lint\results\all_1.csv'

    lo = LintLoader( csvf)
    print( 'raw', len(lo.rawData))

    lo.RemoveDuplicate()
    print( 'reduced', len(lo.reducedData))

    lo.InsertDb( lo.reducedData)