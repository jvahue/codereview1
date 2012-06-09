"""
PC-Lint Tool Manager

Design Assumptions:
1. A .lnt file with all source code files to be analyzed is created during tool setup
2. The .lnt file is located in the PcLint subdir of CodeReview
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

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
import ProjFile
import ViolationDb

from tools.pcLint import PcLintFileTemplates
from tools.pcLint.KsCrLnt import LintLoader
from tools.ToolMgr import ToolSetup, ToolManager
from utils.DateTime import DateTime

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eToolRoot = r'tool\pclint'

eBatchName = r'runLint.bat'
eSrcFilesName = r'srcFiles.lnt'
eResultFile = r'results\result.csv'

ePcLintStdOptions = r"""
// Format Output
-hr2
-width(0,1)
-"format=<*>%f,%i,%l,%t,%n,\q%m\q\n"
-"format_specific=<*>%f,%i,%l,%t,%n,\q%m\q\n"

// Other options
+macros   // (STD) make macros accept string 2*4096
-wlib(1)  // (STD) turn off lib warnings
-e830     // (STD) canonical reference info
-e831     // (STD) canonical reference info
"""

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
class PcLintSetup( ToolSetup):
    def __init__( self, projFile):
        """ Handle all PcLint setup
        """
        assert( isinstance( projFile, ProjFile.ProjectFile))
        self.projFile = projFile
        self.projRoot = projFile.paths['ProjectRoot']

        ToolSetup.__init__( self, self.projRoot)
        self.projToolRoot = os.path.join( self.projRoot, eToolRoot)

        self.fileCount = 0

    #-----------------------------------------------------------------------------------------------
    def CreateProject( self):
        """ Create all of the files needed for this project
            1. runLint.bat - the main file to run PC-Lint
            2. srcFile.lnt - a listing of all the src files
            3. A format file for the lint output to csv files
        """
        assert( isinstance( self.projFile, ProjFile.ProjectFile))

        batTmpl = PcLintFileTemplates.ePcLintBatTemplate
        optTmpl = PcLintFileTemplates.eOptionsTemplate

        toolExe = self.projFile.paths['PcLint']

        # get the PcLint Root
        pcLintRoot = os.path.split( toolExe)[0]

        srcRoots = self.projFile.paths['SrcCodeRoot']
        excludeDirs = self.projFile.exclude['Dirs']
        excludeFiles = self.projFile.exclude['Files_PcLint']
        srcIncludeDirs, srcCodeFiles = self.projFile.GetSrcCodeFiles( srcRoots, ['.c'], excludeDirs, excludeFiles)

        # put all the PcLint Options together
        userOptions = self.projFile.options['PcLint']
        defines = '\n'.join(['-d%s' % i for i in self.projFile.defines])
        undefines = '\n'.join(['-u%s' % i for i in self.projFile.undefines])
        includeDirs = self.projFile.paths['IncludeDirs']

        # STD PC Lint Options
        options  = '%s\n' % (ePcLintStdOptions)

        # Specify all the include dirs
        options += '%s\n' % '\n'.join( ['-i%s' % i for i in srcIncludeDirs+includeDirs])

        # specify the user defined options
        options += '\n// User Options\n%s\n' % ( userOptions)
        options += '\n// User Defines\n%s\n' % ( defines)
        options += '\n// User Undefines\n%s\n' % ( undefines)
        # tag all the extra IndludeDirs not in the SrcCode Root tree as libdirs
        options += '\n// Library Dirs\n%s\n' % '\n'.join( ['+libdir(%s)' % i for i in includeDirs])

        # create the required files
        self.CreateFile( eBatchName, batTmpl % (toolExe, pcLintRoot, eResultFile))
        self.CreateFile( 'srcFiles.lnt', '\n'.join(srcCodeFiles))
        self.CreateFile( 'options.lnt', options)

        self.fileCount = len( srcCodeFiles)

    #-----------------------------------------------------------------------------------------------
    def CreateFile( self, name, content):
        """  creates the named file with the specified contents
        """
        fullPath = os.path.join( self.projToolRoot, name)
        ToolSetup.CreateFile( self, fullPath, content)

    #-----------------------------------------------------------------------------------------------
    def TestCreate(self,):
        # prepend the -i command for PcLint
        includes = ['-i%s' % i.strip() for i in incStr.split('\n') if i.strip() ]
        options['includes'] = '\n'.join(includes)

        options['defines'] = misc

        # get the srcFiles only take .c for testing
        srcFiles = []
        excludedFiles = ('ind_crt0.c','c_cover_ioPWES.c','Etm.c','TestPoints.c')
        for dirPath, dirs, fileNames in os.walk( srcCodeRoot):
            for f in fileNames:
                ffn = os.path.join( dirPath, f)
                if os.path.isfile(ffn) and os.path.splitext( f)[1] == '.c' and f.lower().find('table') == -1:
                    if f not in excludedFiles:
                        srcFiles.append( ffn)

        pcls = PcLintSetup( projRoot)
        pcls.CreateProject( srcFiles, options)

    #-----------------------------------------------------------------------------------------------
    def FileCount( self):
        f = open( os.path.join( self.projToolRoot, 'srcFiles.lnt'), 'r')
        lines = f.readlines()
        f.close()
        self.fileCount = len( lines)

#---------------------------------------------------------------------------------------------------
class PcLint( ToolManager):
    def __init__(self, projFile):
        assert( isinstance( projFile, ProjFile.ProjectFile))
        self.projFile = projFile
        self.projRoot = projFile.paths['ProjectRoot']

        ToolManager.__init__(self, self.projRoot)
        self.projToolRoot = os.path.join( self.projRoot, eToolRoot)

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
        """ Monitor the Analysis and provide status about completion percentage
        """
        # How many files are we analyzing
        ps = PcLintSetup( self.projFile)
        ps.FileCount()

        # call this 50% of the task
        fileCount = 0
        self.analysisPercentComplete = 0
        self.analysisStep = 'Analyzing Files'
        while self.AnalyzeActive():
            for line in self.job.stdout:
                line = line.decode(encoding='windows-1252')
                if line.find( '--- Module:') != -1:
                    fileCount += 1
                    v = ((fileCount/float(ps.fileCount))*100.0) / 2.0
                    self.AnalysisStatusMsg( v)

        # the other 50%
        self.analysisStep = 'Format PcLint Output'
        self.CleanLint()

        self.analysisStep = 'Acquire DB Lock'
        self.AnalysisStatusMsg( 52)
        self.projFile.dbLock.acquire()

        self.analysisStep = 'Load DB'
        self.LoadDb()
        self.AnalysisStatusMsg( 100)
        self.projFile.dbLock.release()

    #-----------------------------------------------------------------------------------------------
    def CleanLint( self):
        """ Load the new Lint info into the DB
            new items
            repeat open items
            repeats closed items
        """
        eFieldCount = 6
        # open the source file
        finName = os.path.join( self.projToolRoot, eResultFile)
        fin = open( finName, 'r', newline='')
        csvIn = csv.reader( fin)

        foutName = os.path.splitext( finName)[0] + '_1.csv'
        fout = open( foutName, 'w',newline='')
        csvOut = csv.writer(fout)

        csvOut.writerow(['Cnt','Filename','Function','Line','Type','ErrNo','Description','Details'])

        lineNum = 0
        details = ''
        cFileName = ''
        for line in csvIn:
            lineNum += 1
            if len( line) > 0:
                if line[0].find('---') == -1:
                    if line[0].find('<*>') == -1:
                        details = ','.join( line)
                    else:
                        # the format puts a '<*>' on the front of each error report to distinguish
                        # it from details
                        line[0] = line[0].replace('<*>', '')

                        if len(line) != eFieldCount:# and l[1:6] == l[6:]:
                            line = line[:eFieldCount]

                        # remove full pathname
                        if line[0] and line[0][0] != '.':
                            path, fn = os.path.split(line[0])
                            subdir = os.path.split( path)[1]
                            if subdir:
                                aFilename = r'%s\%s' % (subdir, fn)
                            else:
                                aFilename = fn
                            line = [aFilename] + line[1:]

                        # replace the unknown file name with current file name
                        if line[0] == eSrcFilesName:
                            line[0] = cFileName

                        opv = [1] + line + [details]
                        # debug
                        dbg = '@'.join(opv[1:])
                        if dbg.find('<*>') != -1:
                            pass
                        csvOut.writerow(opv)
                        details = ''
                else:
                    # capture the filename
                    # line forms are
                    # |--- Module:   <full path file name> (C)
                    # |    --- Wrap-up for Module: <fullpath file name>
                    line = line[0]
                    wrapUp = line.find('Wrap') != -1 and '(W)' or '()'

                    at = line.find( 'Module: ')
                    if at != -1:
                        line = line[at+len( 'Module: '):]
                    parts = line.strip().split()
                    line = parts[0]
                    path, fn = os.path.split(line)
                    subdir = os.path.split( path)[1]
                    cFileName = r'%s\%s %s' % (subdir, fn, wrapUp)

        fout.close()
        fin.close()

        # rename
        os.remove( finName)
        os.rename( foutName, finName)

    #-----------------------------------------------------------------------------------------------
    def LoadDb( self):
        """ We should now have a clean PcLint output to load into the DB
        """
        # open the source file
        finName = os.path.join( self.projToolRoot, eResultFile)

        # open the Violation DB
        self.vDb = ViolationDb.ViolationDb( self.projRoot)
        self.vDb.DebugState( 1)

        # move to the DB
        lintLoader = LintLoader( finName, self.vDb)
        lintLoader.RemoveDuplicate()
        self.analysisPercentComplete = 54

        self.updateTime = datetime.datetime.today()

        items = len(lintLoader.reducedData)
        counter = 0
        for filename,func,line,severity,violationId,desc,details in lintLoader.reducedData:
            self.vDb.Insert( filename,func,severity,violationId,desc,details,line,'PcLint',self.updateTime)
            counter += 1
            pct = (float(counter)/items) * (100-54)
            self.AnalysisStatusMsg( 54 + pct)

        s = """
            select count(*)
            from violations
            where lastReport != ?
            and detectedBy = 'PcLint'
            """
        self.vDb.Execute( s, (self.updateTime,))
        data = self.vDb.GetOne()

        # remove the old PcLint violations
        s = "delete from violations where lastReport != ? and detectedBy = 'PcLint'"
        self.vDb.Execute( s, (self.updateTime,))

        # commit all the changes
        self.vDb.Commit()

        # print stats
        self.insertNew = self.vDb.insertNew
        self.insertUpdate = self.vDb.insertUpdate
        self.insertSelErr = self.vDb.insertSelErr
        self.insertInErr = self.vDb.insertInErr
        self.insertUpErr = self.vDb.insertUpErr
        self.insertDeleted = data[0]

        # and close the DB we are done
        self.vDb.Close()

