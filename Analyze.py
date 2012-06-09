"""
Code review Main
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import datetime
import time

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
import ProjFile

from utils.DB.database import Query
from utils.DB.sqlLite.database import DB_SQLite

from tools.pcLint import PcLint
from tools.u4c import u4c

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
projFile = r'C:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ\G4.crp'

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
def Analyze( projFile, verbose = True):
    start = datetime.datetime.today()
    pf = ProjFile.ProjectFile( projFile)

    pcs = PcLint.PcLintSetup( pf)
    pcs.CreateProject()

    u4s = u4c.U4cSetup( pf)
    u4s.CreateProject()

    pcl = PcLint.PcLint( pf)
    u4co = u4c.U4c( pf)

    status = True
    if u4co.IsReadyToAnalyze():
        pcl.Analyze()
        u4co.Analyze()

        pcl.AnalyzeStatus()
        u4co.AnalyzeStatus()

        while pcl.monitor.active or u4co.monitor.active:
            time.sleep(0.5)
            if verbose: print( 'PcLint: %s U4C: %s' % (pcl.analysisMsg,u4co.analysisMsg))

        for i in ('insertNew','insertUpdate','insertSelErr','insertInErr','insertUpErr','insertDeleted','updateTime',):
            if verbose: print('%s: %s' % (i, str(getattr(pcl, i))))

        end = datetime.datetime.today()
        print('Analysis Completed in %s' % (end - start))
    else:
        if verbose: print('U4C DB is currently open')
        status = False

    return status

if __name__ == '__main__':
    Analyze(projFile)
