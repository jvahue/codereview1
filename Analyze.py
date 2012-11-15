"""
Code review Main
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import datetime
import os
import sys
import time

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------
try:
    import wingdbstub
except ImportError:
    pass

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
import ProjFile

from utils import DateTime
from utils.util import ThreadSignal

#from utils.DB.database import Query
#from utils.DB.sqlLite.database import DB_SQLite

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
        """ Initialize an analyzer object """
        self.abortRequest = False

        if os.path.isfile( projFile):
            self.projFile = ProjFile.ProjectFile( projFile)
            if self.projFile.isValid:
                self.SetStatus( 'Ready')
                self.isValid = True
            else:
                errs = '\n'.join( self.projFile.errors)
                self.SetStatus( 'Error in project file: \n%s' % (errs))
                self.isValid = False
        else:
            self.SetStatus( 'Project file does not exist!')
            self.isValid = False

    #-----------------------------------------------------------------------------------------------
    def SetStatus( self, sts):
        print( sts)
        sys.stdout.flush()
        self.status = sts

    #-----------------------------------------------------------------------------------------------
    def Analyze( self, fullAnalysis = True, pcLintRun=True, u4cRun=True):
        """ Analyze the project file with the tools selected
        """
        status = True
        start = DateTime.DateTime.today()
        self.SetStatus( 'Start Analysis %s - Create Tool Projects' % start)

        # create the tool analysis files
        if pcLintRun:
            pcs = PcLint.PcLintSetup( self.projFile)
            pcs.CreateProject()
        if u4cRun:
            u4s = u4c.U4cSetup( self.projFile)
            u4s.CreateProject()

        self.SetStatus( 'Tool Project Creation Complete - Start Analysis %s' % start)

        # create the tool analyzers
        pcl = PcLint.PcLint( self.projFile, True)
        u4co = u4c.U4c( self.projFile, True)

        if fullAnalysis:
            # check if we can open the DB and stop U4c if running
            r1 = u4co.IsReadyToAnalyze(kill=True)
            if not r1 or u4co.IsReadyToAnalyze():
                u4cThread = ThreadSignal( u4co.RunToolAsProcess, u4co)
                pclThread = ThreadSignal( pcl.RunToolAsProcess, pcl)

                if u4cRun:
                    u4cThread.Go()
                if pcLintRun:
                    pclThread.Go()
                while u4cThread.active or pclThread.active:
                    pcl.abortRequest = self.abortRequest
                    u4co.abortRequest = self.abortRequest

                    time.sleep(1)
                    timeNow = DateTime.DateTime.today()
                    timeNow.ShowMs(False)
                    abortMsg = '[ABORT PENDING]' if self.abortRequest else ''
                    self.SetStatus( '^%s: PcLint: %s%% - U4C: %s%% %s' % (timeNow, pcl.statusMsg,
                                                                          u4co.statusMsg, abortMsg))
            else:
                msg  = 'U4C DB is currently open.\n'
                msg += 'Close the Project then select Run Analysis.\n'
                self.SetStatus( msg)
                status = False
        else:
            u4cThread = ThreadSignal( u4co.LoadViolations, u4co)
            pclThread = ThreadSignal( pcl.LoadViolations, pcl)

            if u4cRun:
                u4cThread.Go()
            if pcLintRun:
                pclThread.Go()
            while u4cThread.active or pclThread.active:
                time.sleep(1)
                timeNow = DateTime.DateTime.today()
                timeNow.ShowMs(False)
                abortMsg = '[ABORT PENDING]' if self.abortRequest else ''
                self.SetStatus(  '^%s: PcLint: %s%% - U4C: %s%% %s' % (timeNow, pcl.statusMsg,
                                                                       u4co.statusMsg, abortMsg))

        end = datetime.datetime.today()
        abortMsg = ' aborted. ' if self.abortRequest else ' '
        m0 = '\nAnalysis%sCompleted in %s\n' % (abortMsg, end - start)

        m1 = pcl.ShowRunStats()
        m2 = u4co.ShowRunStats()

        msg = m0 + '\n'.join(m1 + m2)
        self.SetStatus( msg)

        time.sleep(1)
        return status

#===================================================================================================
if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        projFile = sys.argv[1]
        fullAnalysis = True
        pcRun = True
        u4cRun = True
    else:
        #jvDesk
        #projFile = r'C:\Knowlogic\tools\CR-Projs\G4-A\G4A.crp'
        #projFile = r'C:\Knowlogic\tools\CR-Projs\Rypos\Rypos.crp'

        # PWC desk
        projFile = r'C:\Users\P916214\Documents\Knowlogic\CodeReviewProj\Fast\G4.crp'

        # jvLaptop
        #projFile = r'D:\Knowlogic\Tools\CR-Projs\zzzCodereviewPROJ\G4.crp'

        #projFile = input( 'Enter the project File: ')
        if projFile[0] == '"' and projFile[-1] == '"':
            projFile = projFile[1:-1]

        fullAnalysis = input( 'Do you want to analyze the source code (Y/n): ')
        fullAnalysis = False if fullAnalysis and fullAnalysis.lower()[0] == 'n' else True

        pcRun = input( 'Do you want to Run PcLint (Y/n): ')
        pcRun = False if pcRun and pcRun.lower()[0] == 'n' else True

        u4cRun = input( 'Do you want to Run Knowlogic (Y/n): ')
        u4cRun = False if u4cRun and u4cRun.lower()[0] == 'n' else True

    analyzer = Analyzer(projFile)

    if analyzer.isValid:
        analyzer.Analyze(fullAnalysis, pcRun, u4cRun)
    else:
        print( 'Errors:\n%s' % '\n'.join(analyzer.projFile.errors))

