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

from utils.util import ThreadSignal

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
def Analyze( projFile, fullAnalysis = True, verbose = True):
    status = True
    start = datetime.datetime.today()

    pf = ProjFile.ProjectFile( projFile)

    pcs = PcLint.PcLintSetup( pf)
    pcs.CreateProject()

    u4s = u4c.U4cSetup( pf)
    u4s.CreateProject()

    pcl = PcLint.PcLint( pf)
    u4co = u4c.U4c( pf)

    if fullAnalysis:
        if u4co.IsReadyToAnalyze():
            u4cThread = ThreadSignal( u4co.RunToolAsProcess, u4co)
            pclThread = ThreadSignal( pcl.RunToolAsProcess, pcl)

            u4cThread.Go()
            pclThread.Go()
            while u4cThread.active or pclThread.active:
                time.sleep(0.5)
                if verbose: print('PCL: %s - U4C: %s' % (pcl.statusMsg, u4co.statusMsg))
        else:
            if verbose: print('U4C DB is currently open')
            status = False

    if status:
        u4cThread = ThreadSignal( u4co.LoadViolations, u4co)
        pclThread = ThreadSignal( pcl.LoadViolations, pcl)

        u4cThread.Go()
        pclThread.Go()
        while u4cThread.active or pclThread.active:
            time.sleep(0.5)
            if verbose: print('PCL: %s - U4C: %s' % (pcl.statusMsg, u4co.statusMsg))

        for i in ('insertNew','insertUpdate','insertSelErr','insertInErr','insertUpErr','insertDeleted','updateTime',):
            if verbose: print('%s: %s' % (i, str(getattr(pcl, i))))

        end = datetime.datetime.today()
        print('Analysis Completed in %s' % (end - start))

    return status

if __name__ == '__main__':
    Analyze(projFile)#, False)
