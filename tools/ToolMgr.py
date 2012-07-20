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
from utils import DateTime

import ProjFile as PF
import ViolationDb as VDB

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
    def __init__(self, projFile, toolName, toolDir, isToolRun=False):
        """ Initialize the base class """
        assert(isinstance( projFile, PF.ProjectFile))

        self.projFile = projFile
        self.toolName = toolName

        self.jobCmd = ''
        self.toolProcess = None

        self.vDb = None

        self.insertNew = 0
        self.insertUpdate = 0
        self.insertSelErr = 0
        self.insertInErr = 0
        self.insertUpErr = 0
        self.insertDeleted = 0
        self.unanalyzed = 0

        self.abortRequest = False

        # open a log file for the tool
        self.logName = os.path.join( toolDir, '%s.log' % toolName)
        if isToolRun:
            self.log = open( self.logName, 'w')
        else:
            self.log = None

        self.SetStatusMsg( msg = 'Inactive')

    #-----------------------------------------------------------------------------------------------
    def RunToolAsProcess(self):
        """ Run a Review based on this tools capability.  This is generally a two step process:
          1. Update the tool output
          2. Generate Reivew data
        """
        self.toolProcess = subprocess.Popen( self.jobCmd, bufsize=-1, cwd=self.projToolRoot,
                                     stderr=subprocess.STDOUT,
                                     stdout=subprocess.PIPE)

    #-----------------------------------------------------------------------------------------------
    def AnalyzeActive(self):
        """ is a review actively running
        Note the sleep is to ensure if threads are getting active status they give up control
        """
        status = False
        time.sleep( 0.001)
        if self.toolProcess is not None:
            if self.toolProcess.poll() is None:
                status = True

        return status

    #-----------------------------------------------------------------------------------------------
    def LoadViolations(self):
        """ Load the DB with violations
        """
        if not self.abortRequest:
            # create a connections to the Violation DB
            self.vDb = VDB.ViolationDb( self.projFile.paths[PF.ePathProject])
            self.vDb.DebugState( 1)

            try:
                # the actual work of loading the DB
                self.SpecializedLoad()
            except:
                self.vDb.Close()
                raise

            self.GetUpdateStats()

            # we have to close the DB in the thread it was opened in
            self.vDb.Close()

    #-----------------------------------------------------------------------------------------------
    def Log(self, msg):
        if self.log:
            timeNow = DateTime.DateTime.today()
            if msg[-1] != '\n':
                msg += '\n'
            self.log.write( '%s: %s' % (timeNow, msg))

    #-----------------------------------------------------------------------------------------------
    def LogFlush(self):
        if self.log:
            self.log.flush()

    #-----------------------------------------------------------------------------------------------
    def SpecializedLoad(self):
        """ subclasses define how to monitor their analysis process """
        raise NotImplemented

    #-----------------------------------------------------------------------------------------------
    def Sleep(self, duration=2):
        """ If the tool wants to give up control """
        time.sleep( duration)

    #-----------------------------------------------------------------------------------------------
    def Report(self):
        """ Create a report of the outstanding violations detected by the tool
        """
        raise NotImplemented

    #-----------------------------------------------------------------------------------------------
    def SetStatusMsg(self, v=0, msg=''):
        """ Provide a message that can be displayed by the FE when the analysis is running
        """
        if msg:
            self.analysisStep = msg
            self.sleeper = 0
            self.Log(msg)

        self.sleeper += 1
        if self.sleeper == 500:
            time.sleep( 0.001)
            self.sleeper = 0

        self.percentComplete = v

        self.statusMsg = '%s: %.1f' % (self.analysisStep, v)

    #-----------------------------------------------------------------------------------------------
    def GetUpdateStats(self):
        """ Collect the stats from this run """
        # how many old not reported ones are there
        self.insertNew = self.vDb.insertNew
        self.insertUpdate = self.vDb.insertUpdate
        self.insertSelErr = self.vDb.insertSelErr
        self.insertInErr = self.vDb.insertInErr
        self.insertUpErr = self.vDb.insertUpErr

    #-----------------------------------------------------------------------------------------------
    def GetLogName(self):
        return self.logName

    #-----------------------------------------------------------------------------------------------
    def ShowRunStats(self):
        """ Display what happened during the last run """
        statNames = ('insertNew',
                     'insertUpdate',
                     'insertSelErr',
                     'insertInErr',
                     'insertUpErr',
                     'insertDeleted',
                     'unanalyzed',
                     'updateTime',)

        msg = ['\n%s Stats' % self.toolName]
        for i in statNames:
            msg.append('%s: %s' % (i, str(getattr(self, i, -1))))
        print('\n'.join( msg))

        return msg
