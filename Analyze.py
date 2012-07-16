"""
Code review Main
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import datetime
import os
import socket
import sys
import time

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
import ProjFile

from utils import DateTime
from utils.util import ThreadSignal

from utils.DB.database import Query
from utils.DB.sqlLite.database import DB_SQLite

from tools.pcLint import PcLint
from tools.u4c import u4c

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
class Analyzer:
    def __init__( self, projFile):
        """ Initializ an analyzer object """
        if os.path.isfile( projFile):
            self.projFile = ProjFile.ProjectFile( projFile)
            if self.projFile.isValid:
                self.status = 'Ready'
                self.isValid = True
            else:
                self.status = 'Error'
                self.isValid = False
        else:
            self.status = 'Project file does not exist!'
            self.isValid = False

    #-----------------------------------------------------------------------------------------------
    def Analyze( self, fullAnalysis = True, verbose = True):
        """ Analyze the project file with the tools selected
        """
        status = True
        start = DateTime.DateTime.today()
        if verbose:
            print('Start Analysis %s' % start)

        # create the tool analysis files
        pcs = PcLint.PcLintSetup( self.projFile)
        u4s = u4c.U4cSetup( self.projFile)
        pcs.CreateProject()
        u4s.CreateProject()

        # create the tool analyzers
        pcl = PcLint.PcLint( self.projFile)
        u4co = u4c.U4c( self.projFile)

        if fullAnalysis:
            if u4co.IsReadyToAnalyze():
                u4cThread = ThreadSignal( u4co.RunToolAsProcess, u4co)
                pclThread = ThreadSignal( pcl.RunToolAsProcess, pcl)

                u4cThread.Go()
                pclThread.Go()
                while u4cThread.active or pclThread.active:
                    time.sleep(1)
                    timeNow = DateTime.DateTime.today()
                    timeNow.ShowMs(False)
                    self.status = '%s: PcLint: %s - U4C: %s              ' % (timeNow,
                                                                              pcl.statusMsg,
                                                                              u4co.statusMsg)
                    if verbose:
                        print((' '*100)+'\r', end='') # clear the line
                        print(self.status+'\r', end='')
            else:
                if verbose:
                    self.status = 'U4C DB is currently open'
                    print(self.status)
                status = False
        else:
            u4cThread = ThreadSignal( u4co.LoadViolations, u4co)
            pclThread = ThreadSignal( pcl.LoadViolations, pcl)

            u4cThread.Go()
            pclThread.Go()
            while u4cThread.active or pclThread.active:
                time.sleep(1)
                timeNow = DateTime.DateTime.today()
                timeNow.ShowMs(False)
                self.status = '%s: PcLint: %s - U4C: %s' % (timeNow, pcl.statusMsg, u4co.statusMsg)
                if verbose:
                    print((' '*100)+'\r', end='') #clear the line
                    print(self.status+'\r', end='')

            end = datetime.datetime.today()
            self.status = 'Analysis Completed in %s' % (end - start)

        if verbose:
            pcl.ShowRunStats()
            u4co.ShowRunStats()
            print(self.status)

        return status

#===================================================================================================
if __name__ == '__main__':
    #jvDesk
    #projFile = r'C:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ\G4.crp'
    #projFile = r'C:\Knowlogic\tools\CR-Projs\Rypos\Rypos.crp'

    # PWC desk
    projFile = r'L:\FAST II\control processor\CodeReview\G4.crp'

    # jvLaptop
    #projFile = r'D:\Knowlogic\Tools\CR-Projs\zzzCodereviewPROJ\G4.crp'

    projFile = input( 'Enter the project File: ')
    if projFile[0] == '"' and projFile[-1] == '"':
        projFile = projFile[1:-1]

    analyzer = Analyzer(projFile)

    if analyzer.isValid:
        fullAnalysis = input( 'Do you want to analyze the source code (Y/n): ')
        if fullAnalysis and fullAnalysis.lower()[0] == 'n':
            fullAnalysis = False
        else:
            fullAnalysis = True
        analyzer.Analyze(fullAnalysis)
    else:
        print( 'Errors:\n%s' % '\n'.join(analyzer.projFile.errors))

    print( analyzer.status)

