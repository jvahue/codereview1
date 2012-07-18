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

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
import ProjFile as PF
import ViolationDb as VDB

from tools.pcLint import PcLintFileTemplates
from tools.pcLint.KsCrLnt import LintLoader
from tools.ToolMgr import ToolSetup, ToolManager
from utils.DateTime import DateTime

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eDbDetectId = 'PcLint'

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
        assert( isinstance( projFile, PF.ProjectFile))
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
        assert( isinstance( self.projFile, PF.ProjectFile))

        batTmpl = PcLintFileTemplates.ePcLintBatTemplate
        optTmpl = PcLintFileTemplates.eOptionsTemplate

        toolExe = self.projFile.paths['PcLint']

        # get the PcLint Root
        pcLintRoot = os.path.split( toolExe)[0]

        excludeDirs = self.projFile.exclude['Dirs']
        excludeFiles = self.projFile.exclude['Files_PcLint']
        srcIncludeDirs, srcCodeFiles = self.projFile.GetSrcCodeFiles( ['.c'], excludeDirs, excludeFiles)

        # put all the PcLint Options together
        userOptions = self.projFile.options['PcLint']
        # make sure any defines with spaces are wrapped in ""
        defines = '\n'.join(['++d"%s"' % i for i in self.projFile.defines])
        undefines = '\n'.join(['-u%s' % i for i in self.projFile.undefines])
        includeDirs = self.projFile.paths['IncludeDirs']

        # if any srcIncludeDirs are in the includeDirs remove them
        for i in includeDirs:
            if i in srcIncludeDirs:
                srcIncludeDirs.remove(i)

        # STD PC Lint Options
        options  = '%s\n' % (ePcLintStdOptions)

        # Specify all the include dirs
        options += '%s\n' % '\n'.join( ['-i"%s"' % i for i in srcIncludeDirs+includeDirs])

        # specify the user defined options
        options += '\n// User Options\n%s\n' % ( userOptions)
        options += '\n// User Defines\n%s\n' % ( defines)
        options += '\n// User Undefines\n%s\n' % ( undefines)
        # tag all the extra IndludeDirs not in the SrcCode Root tree as libdirs
        options += '\n// Library Dirs\n%s\n' % '\n'.join( ['+libdir(%s)' % i for i in includeDirs])

        # create the required files
        self.CreateFile( eBatchName, batTmpl % (toolExe, pcLintRoot, eResultFile))
        srcFileData = ['"%s"' % i for i in srcCodeFiles]
        self.CreateFile( 'srcFiles.lnt', '\n'.join(srcFileData))
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
        assert( isinstance( projFile, PF.ProjectFile))
        self.projFile = projFile
        self.projRoot = projFile.paths['ProjectRoot']

        self.projToolRoot = os.path.join( self.projRoot, eToolRoot)

        ToolManager.__init__(self, projFile, eDbDetectId, self.projToolRoot)

    #-----------------------------------------------------------------------------------------------
    def RunToolAsProcess(self):
        """ This function runs a thrid party tool as a process to update any data generated
            by the third party tool.

            This function should be run as a thread by the caller because this will allow
            the caller to report on the status of the process as it runs. (i.e., % complete)
        """
        #self.Log ('Thread %s' % eDbDetectId, os.getpid())

        # How many files are we analyzing
        ps = PcLintSetup( self.projFile)
        ps.FileCount()

        # Run the PC-Lint bat file
        self.jobCmd = '%s' % os.path.join( self.projToolRoot, eBatchName)
        ToolManager.RunToolAsProcess(self)

        # monitor PcLint processing
        fileCount = 0
        self.SetStatusMsg( msg = 'Analyzing Files')
        output = ''
        while self.AnalyzeActive():
            for line in self.job.stdout:
                line = line.decode(encoding='windows-1252')
                self.Log( line)
                self.LogFlush()
                output += line
                if line.find( '--- Module:') != -1:
                    fileCount += 1
                    v = ((fileCount/float(ps.fileCount))*100.0)
                    self.SetStatusMsg( v)

        self.SetStatusMsg( 100)

        self.LoadViolations()

        if fileCount != ps.fileCount:
            self.SetStatusMsg(100, 'Processing Error Occurred - see DB')
        else:
            self.SetStatusMsg(100, 'Processing Complete')

    #-----------------------------------------------------------------------------------------------
    def SpecializedLoad(self):
        """ This function is responsible for loading the violations into the violation DB

            This function should be run as a thread by the caller because this will allow
            the caller to report on the status of the DB Load as it runs. (i.e., % complete)
        """
        self.updateTime = datetime.datetime.today()
        self.CleanLint()
        self.LoadDb()

    #-----------------------------------------------------------------------------------------------
    def CleanLint( self):
        """ Load the new Lint info into the DB
            new items
            repeat open items
            repeats closed items

            TODO: detect errors in processing ... not all files processed
        """
        self.SetStatusMsg( msg = 'Format PC-Lint Output')

        finName = os.path.join( self.projToolRoot, eResultFile)
        eFieldCount = 6

        # see how many lines we need to process
        fin = open( finName, 'r', newline='')
        lines = fin.readlines()
        totalLines = len(lines)
        fin.close()

        # only do this for newly generated data
        if lines[0].strip().find('Cnt') != 0:
            # open the source file
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
                #pct = (float(lineNum)/totalLines) * 100.0
                #self.SetStatusMsg( pct)
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

        # move to the DB
        lintLoader = LintLoader( finName, self.vDb)
        lintLoader.RemoveDuplicate()

        items = len(lintLoader.reducedData)
        try:
            self.SetStatusMsg( msg = 'Acquire DB Lock')
            self.projFile.dbLock.acquire()

            self.SetStatusMsg( msg = 'Load %s Violations' % eDbDetectId)

            pctCtr = 0
            commitSize = 10
            nextCommit = commitSize
            for filename,func,line,severity,violationId,desc,details in lintLoader.reducedData:
                self.vDb.Insert( filename, func, severity, violationId,
                                 desc, details, line, eDbDetectId, self.updateTime)
                pctCtr += 1
                pct = (float(pctCtr)/items) * 99.0
                self.SetStatusMsg( pct)
                if pct > nextCommit:
                    self.vDb.Commit()
                    nextCommit += commitSize

            self.insertDeleted = self.vDb.MarkNotReported( self.toolName, self.updateTime)
            self.unanalyzed = self.vDb.Unanalyzed( self.toolName)

        except:
            raise
        finally:
            self.projFile.dbLock.release()
            pass
