"""
SciTool Understand for C/C++ Tool Manager

Design Assumptions:
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import csv
import datetime
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
import ProjFile as PF
import ViolationDb

from tools.u4c import u4cDbWrapper as udb
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
        assert( isinstance( projFile, PF.ProjectFile))
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
        excludeDirs = self.projFile.exclude['Dirs']
        excludeFiles = self.projFile.exclude['Files_U4c']
        incDirs, srcFiles = self.projFile.GetSrcCodeFiles( srcRoots, ['.c','.h'], excludeDirs, excludeFiles)

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
        self.CreateFile( eSrcFilesName, '\n'.join(srcFiles))

        self.fileCount = len( srcFiles)

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
        assert( isinstance( projFile, PF.ProjectFile))
        self.projFile = projFile
        self.projRoot = projFile.paths[PF.ePathProject]

        ToolManager.__init__(self, self.projRoot)

        self.projToolRoot = os.path.join( self.projRoot, eToolRoot)

        self.dbName = os.path.join( self.projToolRoot, eDbName)

    #-----------------------------------------------------------------------------------------------
    def IsReadyToAnalyze(self):
        """ we are about to create the db and put stuff in it. Make sure it is not locked by some
            with U4c GUI open
        """
        # TODO: if U4C fixes the db open we cna use that to findout if some one has the Db open
        #       right now we will try to delete it, and hopefully get an exception
        try:
            if os.path.isfile( self.dbName):
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
        try:
            fileList = []
            analyzing = False
            fileCount = 0
            self.analysisStep = 'Analyzing Files'
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
                            v = 100 - (len(fileList)/float(fileCount)*100.0)
                            self.AnalysisStatusMsg( v)

            # now run the review of the u4c DB which is the other half of this process
            # get the file list to check
            srcRoots = self.projFile.paths[PF.ePathSrcRoot]
            excludeDirs = self.projFile.exclude[PF.eExcludeDirs]
            excludeFiles = self.projFile.exclude[PF.eExcludeU4c]
            x, self.srcFiles = self.projFile.GetSrcCodeFiles(srcRoots, ['.h','.c'],
                                                             excludeDirs, excludeFiles)

            # open the Violation DB
            self.vDb = ViolationDb.ViolationDb( self.projRoot)
            self.vDb.DebugState( 1)

            self.updateTime = datetime.datetime.today()
            self.udb = udb.U4cDb( self.dbName)
            # 12.5 % Each
            self.analysisStep = 'Acquire DB Lock'
            self.AnalysisStatusMsg( 0)
            self.projFile.dbLock.acquire()

            self.analysisStep = 'Metric'
            self.AnalysisStatusMsg( 0)
            self.MetricChecks()
            #self.FormatChecks()
            #self.NamingChecks()
            #self.LanguageRestriction()
            self.vDb.Close()

            self.AnalysisStatusMsg( 100)
            self.projFile.dbLock.release()
        except:
            self.vDb.Close()
            raise

    #-----------------------------------------------------------------------------------------------
    def MetricChecks( self):
        self.LenghtChecks()

    #-----------------------------------------------------------------------------------------------
    def LenghtChecks(self):
        """ This function verifies all of the length limits are met on a file by fial basis.
        """
        fileLimit = self.projFile.metrics[PF.eMetricFile]
        funcLimit = self.projFile.metrics[PF.eMetricFunc]

        counter = 0
        totalFiles = len(self.srcFiles)
        for i in self.srcFiles:
            counter += 1
            self.AnalysisStatusMsg( (counter/float(totalFiles)*100))

            # compute the relative path from a srcRoot
            for sr in self.projFile.paths[PF.ePathSrcRoot]:
                fn = i.replace(sr, '')
                if fn[0] == r'\\': fn = fn[1:]
            rpfn = fn
            fn = os.path.split(rpfn)[1]

            # Get file information
            if os.path.splitext( fn) == '.c':
                funcInfo = self.udb.GetFuncInfo( fn)
            else:
                funcInfo = {}
            func = 'N/A'

            f = open(i, 'r')
            lines = f.readlines()
            f.close()

            # check to file size violation
            fileSize = len(lines)
            if fileSize > fileLimit:
                line = fileSize
                severity = 'Error'
                violationId = 'Metric-File'
                desc = 'File Length Exceeded: %s' % (fn)
                details = 'Total line count (%d) exceeds project maximum (%d)' % (fileSize,
                                                                                  fileLimit)
                self.vDb.Insert(rpfn, func, severity, violationId, desc,
                                details, line, 'U4C', self.updateTime)
                self.vDb.Commit()

            # check the lenght of each line
            self.CheckLineLength( rpfn, funcInfo, lines)


    #-----------------------------------------------------------------------------------------------
    def CheckLineLength(self, rpfn, funcInfo, lines):
        # check all line lengths
        fileSize = len(lines)
        fn = os.path.split(rpfn)[1]
        lineLimit = self.projFile.metrics[PF.eMetricLine]
        func = 'N/A'

        for lineNumber in range(0,fileSize):
            txt = lines[lineNumber].rstrip()
            lineLen = len(txt)
            if lineLen > lineLimit:
                severity = 'Error'
                violationId = 'Metric-Line'
                desc = 'Line Length in %s line %d' % (fn, lineNumber)
                details = '%3d: %s' % (lineLen, txt.strip())
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                                 details, lineNumber, 'U4C', self.updateTime)
        self.vDb.Commit()

    #-----------------------------------------------------------------------------------------------
    def FormatChecks(self):
        pass

    #-----------------------------------------------------------------------------------------------
    def NamingChecks(self):
        pass

    #-----------------------------------------------------------------------------------------------
    def LanguageRestriction(self):
        # excluded functions
        # restricted functions
        pass


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

if __name__ == '__main__':
    TestRun()