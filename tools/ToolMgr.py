"""
Tool Manager Base Classes

This class defines the interface to a tool manager.  Tool managers are used to control a new tool
in a common way such that the upper level systems does not care what tool it is using to perform
violation checks, review violations, etc.

1. Setup
2. Data
3. View

"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import io
import os
import subprocess
import time

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
from utils.util import ThreadSignal

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
class ToolSetup:
    """
    """
    def __init__(self, projRoot):
        self.projRoot = projRoot

    #-----------------------------------------------------------------------------------------------
    def CreateProject( self):
        raise NotImplemented

    #-----------------------------------------------------------------------------------------------
    def CreateFile( self, name, content):
        """  creates the named file with the specified contents
        """
        # make sure the directory exists where we are putting this
        path, fn = os.path.split(name)
        if not os.path.isdir( path):
            os.makedirs( path)

        f = open( name, 'w')
        f.write( content)
        f.close()

#---------------------------------------------------------------------------------------------------
class ToolManager:
    """
    I/F defintion for all tool managers
    """
    #-----------------------------------------------------------------------------------------------
    def __init__(self, projRoot):
        self.projRoot = projRoot
        self.jobCmd = ''
        self.job = None

    #-----------------------------------------------------------------------------------------------
    def Analyze(self):
        """ Run a Review based on this tools capability.  This is generally a two step process:
          1. Update the tool output
          2. Generate Reivew data
        """
        self.analysisPercentComplete = 0
        self.job = subprocess.Popen( self.jobCmd, bufsize=-1, cwd=self.projToolRoot,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    #-----------------------------------------------------------------------------------------------
    def AnalyzeActive(self):
        """ is a review actively running
        Note the sleep is to ensure if threads are getting active status they give up control
        """
        status = False
        time.sleep( 0.001)
        if self.job is not None:
            if self.job.poll() is None:
                status = True

        return status

    #-----------------------------------------------------------------------------------------------
    def AnalyzeStatus(self):
        """ Run the sub-class analysis monitor in a thread
        """
        # Monitor the sub-process run this is 50% of this activity
        self.monitor = ThreadSignal( self.MonitorAnalysis, self)
        self.analysisStep = ''
        self.analysisPercentComplete = 0.0
        self.analysisMsg = 'Starting'
        self.monitor.Go()

    #-----------------------------------------------------------------------------------------------
    def PollReview(self):
        """ return the output of the job while it runs
        """
        out = self.job.stdout.read()
        return out

    #-----------------------------------------------------------------------------------------------
    def MonitorAnalysis(self):
        """ subclasses define how to monitor their analysis process """
        raise NotImplemented

    #-----------------------------------------------------------------------------------------------
    def Report(self):
        """ Create a report of the outstanding violations detected by the tool
        """
        raise NotImplemented

    #-----------------------------------------------------------------------------------------------
    def AnalysisStatusMsg(self, v):
        """ Provide a message that can be displayed by the FE when the analysis is running
        """
        self.analysisPercentComplete = v
        self.analysisMsg = '%s: %.1f' % (self.analysisStep, v)




