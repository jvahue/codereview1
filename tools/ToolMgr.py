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
import os
import subprocess

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------

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
    def Review(self):
        """ Run a Review based on this tools capability.  This is generally a two step process:
          1. Update the tool output
          2. Generate Reivew data
        """
        self.job = subprocess.Popen( self.jobCmd, bufsize=-1, cwd=self.projToolRoot, shell=True)#,
                                     #stdout=subprocess.PIPE)#, stderr=subprocess.PIPE)

    #-----------------------------------------------------------------------------------------------
    def ReviewActive(self):
        """ is a review actively running """
        status = False
        if self.job is not None:
            if self.job.poll() is None:
                status = True
            else:
                # collect all the final output and result code from the process
                pass
        else:
            self.job

        return status

    #-----------------------------------------------------------------------------------------------
    def PollReview(self):
        """ return the output of the job while it runs
        """
        out = self.job.stdout.read()
        return out

    #-----------------------------------------------------------------------------------------------
    def Analyze(self):
        """ This allows a user to analyze the results.  Data is provided to the associated
            ToolViewer to allow the user to see the results and perform any analysis needed.
        """
        raise NotImplemented

    #-----------------------------------------------------------------------------------------------
    def Report(self):
        """ Create a report of the outstanding violations detected by the tool
        """
        raise NotImplemented





