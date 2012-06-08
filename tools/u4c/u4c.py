"""
SciTool Understand for C/C++ Tool Manager

Design Assumptions:
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import csv
import os
import sys
import time

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------
import understand

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
import ProjFile
import ViolationDb

from tools.u4c import U4cFileTemplates
from tools.ToolMgr import ToolSetup, ToolManager
from utils.DateTime import DateTime

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eToolRoot = r'tool\u4c'
eDbName = 'db.udb'

eBatchName = r'runU4c.bat'
eU4cCmdFileName = r'u4cCmds.txt'
eSrcFilesName = r'srcFiles.lnt'

eResultFile = r'results\result.csv'

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
class U4cSetup( ToolSetup):
    def __init__( self, projFile):
        """ Handle all U4c setup
        """
        assert( isinstance( projFile, ProjFile.ProjectFile))
        self.projFile = projFile
        self.projRoot = projFile.paths['ProjectRoot']

        ToolSetup.__init__( self, self.projRoot)
        self.projToolRoot = os.path.join( self.projRoot, eToolRoot)

    #-----------------------------------------------------------------------------------------------
    def CreateProject( self):
        """ Create all of the files needed for this project
        """
        batTmpl = U4cFileTemplates.eU4cBatTemplate
        optTmpl = U4cFileTemplates.eCmdTemplate

        toolExe = self.projFile.paths['U4c']

        cmdFilePath = os.path.join( self.projToolRoot, eU4cCmdFileName)

        srcRoots = self.projFile.paths['SrcCodeRoot']
        excludeFiles = self.projFile.exclude['Files_U4c']
        srcIncludeDirs, srcCodeFiles = self.GetSrcCodeFile( srcRoots, ['.c', '.h'], excludeFiles)

        # U4c Option definitions
        options = {}
        options['C++Includes'] = self.projFile.paths['IncludeDirs']
        options['C++Macros'] = self.projFile.defines
        options['C++Undefined'] = self.projFile.undefines
        options = self.ConvertOptions( options)

        # create the required files
        self.CreateFile( eBatchName, batTmpl % (toolExe, cmdFilePath))
        cmdContents = optTmpl % (os.path.join( self.projToolRoot, eDbName),
                                 os.path.join( self.projToolRoot, eSrcFilesName),
                                 '\n'.join(options))
        self.CreateFile( eU4cCmdFileName, cmdContents)
        self.CreateFile( eSrcFilesName, '\n'.join(srcCodeFiles))

        self.fileCount = len( srcCodeFiles)

    #-----------------------------------------------------------------------------------------------
    def ConvertOptions( self, options):
        """ Turn a dictionary of option into a single list of und commands
            option => [item1, item2]
              becomes
            settings -option item1
            settings -optionAdd item2
        """
        optionList = []
        for option in options:
            optionData = options[option]
            isFirst = True
            for item in optionData:
                add = '' if isFirst else 'Add'
                isFirst = False
                optionList.append('settings -%s %s' % ( option+add, item))
        return optionList

    #-----------------------------------------------------------------------------------------------
    def CreateFile( self, name, content):
        """  creates the named file with the specified contents
        """
        fullPath = os.path.join( self.projToolRoot, name)
        ToolSetup.CreateFile( self, fullPath, content)

    #-----------------------------------------------------------------------------------------------
    def FileCount( self):
        f = open( os.path.join( self.projToolRoot, 'srcFiles.lnt'), 'r')
        lines = f.readlines()
        f.close()
        self.fileCount = len( lines)

#---------------------------------------------------------------------------------------------------
class U4c( ToolManager):
    def __init__(self, projFile):
        assert( isinstance( projFile, ProjFile.ProjectFile))
        self.projFile = projFile
        self.projRoot = projFile.paths['ProjectRoot']

        ToolManager.__init__(self, self.projRoot)

        self.projToolRoot = os.path.join( self.projRoot, eToolRoot)

        self.dbName = os.path.join( self.projToolRoot, eDbName)

    #-----------------------------------------------------------------------------------------------
    def IsReadyToAnalyze(self):
        """ we are about to create the db and put stuff in it make sure it is not locked by some
            with U4c GUI open
        """
        # TODO: if U4C fixes the db open we cna use that to findout if some one has the Db open
        #       right now we will try to delete it, and hopefully get an exception
        try:
            os.remove( self.dbName)
            status = True
        except OSError:
            status = False

        return status

    #-----------------------------------------------------------------------------------------------
    def Analyze(self):
        """ Run a Review based on this tools capability.  This is generally a two step process:
          1. Update the tool output
          2. Generate Reivew data
        """
        # Run the PC-Lint bat file
        self.jobCmd = '%s' % os.path.join( self.projToolRoot, eBatchName)
        ToolManager.Analyze(self)

    #-----------------------------------------------------------------------------------------------
    def MonitorAnalysis(self):
        """ thread that does the monitoring and completes the analysis
        """
        fileList = []
        analyzing = False
        fileCount = 0
        while self.AnalyzeActive():
            for line in self.job.stdout:
                line = line.decode(encoding='windows-1252').strip()
                if line == 'Analyze':
                    analyzing = True
                    fileCount = len( fileList)
                elif line.find( 'File: ') != -1:
                    line = line.replace('File: ', '').replace(' has been added.', '')
                    fileList.append(line)
                else:
                    if line in fileList:
                        fileList.remove( line)
                        self.analysisPercentComplete = 50.0 - ((len(fileList)/float(fileCount)*100.0)/2.0)

        # now run the review of the u4c DB which is the other half of this process


    #-----------------------------------------------------------------------------------------------
    def LoadDb( self):
        """ We should now have a clean PcLint output to load into the DB
        """
        # open the source file
        finName = os.path.join( self.projToolRoot, eResultFile)

        # open the PCLint DB
        sl3 = ViolationDb.ViolationDb( self.projRoot)
        sl3.DebugState( 1)

        # move to the DB
        lintLoader = LintLoader( finName, sl3)
        lintLoader.RemoveDuplicate()
        removed, updateTime = lintLoader.InsertDb( lintLoader.reducedData)

        # print stats
        print( 'Inserted %5d New' % sl3.insertNew)
        print( 'Updated  %5d Records' % sl3.insertUpdate)
        print( 'Select Errors: %d' % sl3.insertSelErr)
        print( 'Insert Errors: %d' % sl3.insertInErr)
        print( 'Update Errors: %d' % sl3.insertUpErr)

        # remove the old PcLint violations
        s = "delete from violations where lastReport != ? and detectedBy = 'PcLint'"
        sl3.Execute( s, (updateTime,))
        sl3.Commit()
        print( 'Removed %d Old Records - %s' % (removed, updateTime))

#========================================================================================================================
import socket
host = socket.gethostname()

if host == 'Jeff-Laptop':
    projRoot = r'D:\Knowlogic\zzzCodereviewPROJ'
    srcCodeRoot = r'D:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP'
    incStr = r"""
    D:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\GhsInclude
    """
else:
    projRoot = r'C:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ'
    srcCodeRoot = r'C:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\G4_CP'
    incStr = r"""
    C:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\GhsInclude
    """

# these function simulate front end processing
def TestCreate():
    options = {}
    # include directories
    includes = [i.strip() for i in incStr.split('\n') if i.strip() ]
    options['C++Includes'] = includes

    # macro definitions
    options['C++Macros'] = []
    options['C++Undefined'] = []

    # get the srcFiles only take .c for testing
    srcFiles = []
    excludedFiles = ('ind_crt0.c', 'ind_startup.h', 'indsyscl.h',
                     'c_cover_ioPWES.c',
                     'Etm.h', 'Etm.c',
                     'TestPoints.c')
    for dirPath, dirs, fileNames in os.walk( srcCodeRoot):
        for f in fileNames:
            ffn = os.path.join( dirPath, f)
            if os.path.isfile(ffn):
                if f not in excludedFiles and os.path.splitext( f)[1] in ('.h', '.c'):
                    srcFiles.append( ffn)

    u4cs = U4cSetup( projRoot)
    u4cs.CreateProject( srcFiles, options)

def TestRun():

    start = DateTime.today()
    tool = U4c( projRoot)
    tool.Analyze()
    tool.AnalyzeStatus()
    while tool.monitor.active:
        time.sleep(0.5)
        print( 'U4C Complete: %.1f' % tool.analysisPercentComplete)
    end = DateTime.today()
    delta = end - start
    print('U4C Processing: %s' % delta)
