"""
Code review Main
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import time

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
from utils.DB.database import Query
from utils.DB.sqlLite.database import DB_SQLite

from tools.pcLint import PcLint
from tools.u4c import u4c

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
projRoot = r'D:\Knowlogic\zzzCodereviewPROJ'
srcCodeRoot = r'D:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP'

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------

projRoot = r'C:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ'

def Test():
    pcl = PcLint.PcLint( projRoot)
    u4co = u4c.U4c( projRoot)

    pcl.Analyze()
    u4co.Analyze()

    pcl.AnalyzeStatus()
    u4co.AnalyzeStatus()

    while pcl.monitor.active or u4co.monitor.active:
        time.sleep(0.5)
        print( 'PcLint: %.1f U4C: %.1f' % (pcl.analysisPercentComplete,u4co.analysisPercentComplete))

    for i in ('insertNew','insertUpdate','insertSelErr','insertInErr','insertUpErr','insertDeleted','updateTime',):
        print('%s: %s' % (i, str(getattr(pcl, i))))


Test()
