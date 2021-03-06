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
import re

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
import ProjFile as PF

from tools.pcLint import PcLintFileTemplates
from tools.pcLint.KsCrLnt import LintLoader
from tools.ToolMgr import ToolSetup, ToolManager

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
-wlib(0)  // (STD) turn off all lib warnings
-e830     // (STD) canonical reference info
-e831     // (STD) canonical reference info

//+vf
+libclass(angle, ansi)

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
        self.projRoot = projFile.paths[PF.ePathProject]

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

        toolExe = self.projFile.paths['PcLint']

        # get the PcLint Root
        pcLintRoot = os.path.split( toolExe)[0]

        excludeDirs = self.projFile.exclude['Dirs']
        excludeFiles = self.projFile.exclude['Files_PcLint']
        srcIncludeDirs, srcCodeFiles = self.projFile.GetSrcCodeFiles( ['.c','.cpp'],
                                                                      excludeDirs, excludeFiles)

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

        # Specify all the include dirs
        options  = '%s\n' % '\n'.join( ['-i"%s"' % i for i in srcIncludeDirs+includeDirs])

        # tag all the extra IncludeDirs as libdir so PC-LINT does not report errors against them
        options += '\n// Library Dirs\n%s\n' % '\n'.join( ['+libdir(%s)' % i for i in includeDirs])
        # make sure this is last to ensure these are not treated as library dirs
        options += '\n// Src Library Dirs\n%s\n' % '\n'.join( ['-libdir(%s)' % i for i in srcIncludeDirs])

        # STD PC Lint Options
        options += '%s\n' % (ePcLintStdOptions)

        # specify the user defined options
        # - have these alst to over ride any of our computed options
        options += '\n// User Options\n%s\n' % ( userOptions)
        options += '\n// User Defines\n%s\n' % ( defines)
        options += '\n// User Undefines\n%s\n' % ( undefines)

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
    def FileCount( self):
        f = open( os.path.join( self.projToolRoot, 'srcFiles.lnt'), 'r')
        lines = f.readlines()
        f.close()
        self.fileCount = len( lines)

#---------------------------------------------------------------------------------------------------
class PcLint( ToolManager):
    def __init__(self, projFile, isToolRun=False):
        assert( isinstance( projFile, PF.ProjectFile))
        self.projFile = projFile
        self.projRoot = projFile.paths['ProjectRoot']

        self.projToolRoot = os.path.join( self.projRoot, eToolRoot)

        ToolManager.__init__(self, projFile, eDbDetectId, self.projToolRoot, isToolRun)

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
        moduleList = []
        fileCount = 0
        self.SetStatusMsg( msg = 'Analyzing Files')
        while self.AnalyzeActive():
            for line in self.toolProcess.stdout:
                line = line.decode(encoding='windows-1252')
                self.Log( line)
                self.LogFlush()
                if line.find( '--- Module:') != -1:
                    mName = line.replace('--- Module:', '').strip()
                    if mName not in moduleList:
                        moduleList.append(mName)
                        fileCount += 1
                        v = ((fileCount/float(ps.fileCount))*100.0)
                        self.SetStatusMsg( v)

        if fileCount == ps.fileCount:
            self.SetStatusMsg( 100)
            self.LoadViolations()
            self.SetStatusMsg(100, 'Processing Complete')
        else:
            # collect the last 20 lines from the result file and put them in the log file
            finName = os.path.join( self.projToolRoot, eResultFile)
            f = open( finName, 'r')
            lines = f.readlines()
            at = -1
            while abs(at) < len(lines) and (lines[at].find( '--- Module:') == -1 or at < -20):
                at -= 1

            for i in lines[at:]:
                self.Log(i)

            self.LogFlush()

            self.SetStatusMsg(100, 'Processing Error (see log)')

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
            <details>
            <*>Filename,function,line,Warning,641,"Converting enum 'SYS_MODE_IDS' to 'int'"
        """
        eFn, eFunc, eLine, eType, eViol, eDesc = range(0,6)

        gWrapUp = False
        self.SetStatusMsg( msg = 'Format PC-Lint Output')

        finName = os.path.join( self.projToolRoot, eResultFile)
        eFieldCount = 6

        # see how many lines we need to process
        fin = open( finName, 'r', newline='')
        lines = fin.readlines()
        fin.close()

        # only do this for newly generated data
        if lines and lines[0].strip().find('Cnt') != 0:
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
                    if line[eFn].find('---') == -1:
                        if line[eFn].find('<*>') == -1:
                            details = ','.join( line)
                        else:
                            # the format puts a '<*>' on the front of each error report to
                            # distinguish it from details
                            line[eFn] = line[eFn].replace('<*>', '')

                            if len(line) != eFieldCount:# and l[1:6] == l[6:]:
                                line = line[:eFieldCount]

                            if gWrapUp:
                                # Global Wrap-up does not have filename,line# in the usual place
                                # eq, Symbol 'foo' (line X, file <filename>) not referenced
                                # set filename = <filename> and lineNumber = X
                                if line[eFn] == '':
                                    # find parens in desc from reverse because these exist
                                    # ext 'foo(p1, p2, ..)' (line X, file foo.c, module foo.c) desc"
                                    op = line[eDesc].rfind('(')
                                    cp = line[eDesc].rfind(')')
                                    if op != -1 and cp != -1:
                                        data = line[eDesc][op+1:cp]
                                        parts = data.split(',')
                                        if len( parts) >= 2:
                                            line[eLine] = parts[0].replace('line ', '').strip()
                                            line[eFn] = parts[1].replace('file', '').strip()
                                        else:
                                            pass

                            # remove full pathname
                            if line[eFn] and line[eFn][0] != '.':
                                path, fn = os.path.split(line[eFn])
                                srcRoot = self.projFile.paths[PF.ePathSrcRoot]
                                for sd in srcRoot:
                                    subdir = path.replace(sd, '')
                                    if subdir != path:
                                        # make sure this is not interpreted as an absolute path
                                        if subdir and subdir[0] in ('\\', r'/'):
                                            subdir = subdir[1:]
                                        break
                                #subdir = os.path.split( path)[1]
                                if subdir:
                                    aFilename = r'%s\%s' % (subdir, fn)
                                else:
                                    aFilename = fn
                                line = [aFilename] + line[1:]

                            # replace the unknown file name with current file name
                            if line[eFn] == eSrcFilesName:
                                line[eFn] = cFileName

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
                        wrapUp = line.find('--- Wrap') != -1 and ' (W)' or ' ()'

                        if line.find('--- Global Wrap') != -1:
                            gWrapUp = True
                        else:
                            gWrapUp = False

                        at = line.find( 'Module: ')
                        if at != -1:
                            line = line[at+len( 'Module: '):]

                        line = line.replace('(C)', '').strip()
                        cFileName, title = self.projFile.RelativePathName(line)
                        cFileName += wrapUp

            fout.close()
            fin.close()

            # rename
            tmp = finName + '.txt'
            if os.path.isfile(tmp):
                os.remove(tmp)
            os.rename( finName, tmp)
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
                # insert relative path names for all file references
                desc = self.CleanFpfn( desc)

                if self.abortRequest:
                    break

                self.vDb.Insert( filename, func, severity, violationId,
                                 desc, details, line, eDbDetectId, self.updateTime)
                pctCtr += 1
                pct = (float(pctCtr)/items) * 99.0
                self.SetStatusMsg( pct)
                if pct > nextCommit:
                    self.vDb.Commit()
                    nextCommit += commitSize

            if not self.abortRequest:
                self.insertDeleted = self.vDb.MarkNotReported( self.toolName, self.updateTime)
                self.unanalyzed = self.vDb.Unanalyzed( self.toolName)

        except:
            raise
        finally:
            self.vDb.Commit()
            self.projFile.dbLock.release()
            pass

    #-----------------------------------------------------------------------------------------------
    def CleanFpfn( self, desc):
        """ This function cleans out any full path file names and creates relative path file names
            for names in the description.

            PC-Lint precedes file names with 'file' and 'module' in its descriptions
            e.g.,
            [Reference: file D:\knowlogic\FAST\dev\CP\drivers\FPGA.c: line 559]
            (line 62, file D:\knowlogic\FAST\dev\CP\drivers\RTC.c)
            (line 61, file <path>\drivers\EvaluatorInterface.h, module <path>\application\AircraftConfigMgr.c)
        """
        debug = False
        desc0 = desc
        srcRoots = self.projFile.paths[PF.ePathSrcRoot]
        incRoots = self.projFile.paths[PF.ePathInclude]

        # compute the relative path from a srcRoot
        for theDirs, thePattern in ((srcRoots, '<srcRoot>'), (incRoots, '<incRoot>')):
            for sr in theDirs:
                srl = sr.lower()
                # replace all paths in the description
                while True:
                    dl = desc.lower()
                    at = dl.find( srl)
                    if at != -1:
                        end = at + len(srl)
                        desc = desc[0:at] + thePattern + desc[end:]
                    else:
                        break

        if debug and desc0 != desc:
            print( 'Was: %s\n Is:%s' %  (desc0, desc))

        return desc

