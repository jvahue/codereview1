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
    def __init__(self, projFile, verbose=False):
        assert( isinstance( projFile, PF.ProjectFile))
        self.projFile = projFile
        self.projRoot = projFile.paths[PF.ePathProject]

        ToolManager.__init__(self, self.projRoot)

        self.projToolRoot = os.path.join( self.projRoot, eToolRoot)

        self.dbName = os.path.join( self.projToolRoot, eDbName)

        self.verbose = verbose

        # this holds all the file/function info data
        self.fileFuncInfo = {}

    #-----------------------------------------------------------------------------------------------
    def IsReadyToAnalyze(self):
        """ we are about to create the db and put stuff in it. Make sure it is not locked by some
            with U4c GUI open
        """
        # TODO: if U4C fixes the db open we can use that to find out if some one has the Db open
        #       right now we will try to delete it, and hopefully get an exception
        try:
            if os.path.isfile( self.dbName):
                os.remove( self.dbName)
            status = True
        except OSError:
            status = False

        return status

    #-----------------------------------------------------------------------------------------------
    def RunToolAsProcess(self):
        """ This function runs a thrid party tool as a process to update any data generated
            by the third party tool.

            This function should be run as a thread by the caller becuase this will allow
            the caller to report on the status of the process as it runs. (i.e., % complete)
        """
        # Run the PC-Lint bat file
        self.jobCmd = '%s' % os.path.join( self.projToolRoot, eBatchName)
        ToolManager.RunToolAsProcess(self)

        fileCount = 0
        fileList = []
        analyzing = False
        self.SetStatusMsg( msg = 'Parsing Source Files')
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
                        self.SetStatusMsg( v)

        self.LoadViolations()

    #-----------------------------------------------------------------------------------------------
    def LoadViolations(self):
        """ This function is responsible for loading the violations into the violation DB

            This function should be run as a thread by the caller because this will allow
            the caller to report on the status of the DB Load as it runs. (i.e., % complete)
        """
        # now run the review of the u4c DB which is the other half of this process
        # get the file list to check
        self.SetStatusMsg( msg = 'Open U4C DB')
        srcRoots = self.projFile.paths[PF.ePathSrcRoot]
        excludeDirs = self.projFile.exclude[PF.eExcludeDirs]
        excludeFiles = self.projFile.exclude[PF.eExcludeU4c]
        x, self.srcFiles = self.projFile.GetSrcCodeFiles(srcRoots, ['.h','.c'],
                                                         excludeDirs, excludeFiles)
        try:
            self.updateTime = datetime.datetime.today()

            # open the Violation DB
            self.vDb = ViolationDb.ViolationDb( self.projRoot)
            self.vDb.DebugState( 1)

            self.SetStatusMsg( msg = 'Open U4C DB')
            self.udb = udb.U4cDb( self.dbName)

            self.SetStatusMsg( msg = 'Acquire DB Lock')
            self.projFile.dbLock.acquire()

            #self.MetricChecks()
            #self.FormatChecks()
            #self.NamingChecks()
            self.LanguageRestriction()

            # we have to close the DB in the thread it was opened in
            self.vDb.Close()

            self.SetStatusMsg( 100)
            self.projFile.dbLock.release()
        except:
            self.vDb.Close()
            raise

    #-----------------------------------------------------------------------------------------------
    def MetricChecks(self):
        """ This function verifies all of the length limits are met on a file by fail basis.
        """
        self.SetStatusMsg( msg = 'Metric Checks')
        fileLimit = self.projFile.metrics[PF.eMetricFile]

        counter = 0
        totalFiles = len(self.srcFiles)
        for i in self.srcFiles:
            counter += 1
            self.SetStatusMsg( (counter/float(totalFiles)*100))

            # compute the relative path from a srcRoot
            rpfn, fn = self.projFile.RelativePathName( i)

            # Get file/function information
            funcInfo = self.udb.GetFileFunctionInfo( fn)
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

            # check the function metrics
            self.CheckFunctionMetrics( rpfn, funcInfo)

            # check the length of each line
            self.CheckLineLength( rpfn, funcInfo, lines)

    #-----------------------------------------------------------------------------------------------
    def CheckFunctionMetrics(self, rpfn, funcInfo):
        """ Check all the function metrics
        """
        funcLimit = self.projFile.metrics[PF.eMetricFunc]
        mccabeLimit = self.projFile.metrics[PF.eMetricMcCabe]
        nestingLimit = self.projFile.metrics[PF.eMetricNesting]
        returnLimit = self.projFile.metrics[PF.eMetricReturns]

        severity = 'Error'
        for func in funcInfo:
            info = funcInfo[func]
            u4cLine = info['start']

            # this is the total count of lines in the function including comments
            lines = info['metrics']['CountLine']
            if lines > funcLimit:
                violationId = 'Metric-Func'
                desc = 'Function Length exceeded in %s' % (func)
                details = 'Total Line Count %d exceeds %d' % (lines, funcLimit)
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                    details, u4cLine, 'U4C', self.updateTime)

            mccabe = info['metrics']['Cyclomatic']
            if mccabe > mccabeLimit:
                violationId = 'Metric-Cyclomatic'
                desc = 'Function Cyclomatic Complexity exceeded in %s' % (func)
                details = 'Cyclomatic Complexity %d exceeds %d' % (mccabe, mccabeLimit)
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                    details, u4cLine, 'U4C', self.updateTime)

            nesting = info['metrics']['MaxNesting']
            if nesting > nestingLimit:
                violationId = 'Metric-Nesting'
                desc = 'Function Nesting exceeded in %s' % (func)
                details = 'Nesting Levels %d exceeds %d' % (nesting, nestingLimit)
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                    details, u4cLine, 'U4C', self.updateTime)

            returns = info['returns']
            if returns > returnLimit:
                violationId = 'Metric-Returns'
                desc = 'Function Return Points exceeded in %s' % (func)
                details = 'Return Points %d exceeds %d' % (returns, returnLimit)
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                    details, u4cLine, 'U4C', self.updateTime)



    #-----------------------------------------------------------------------------------------------
    def CheckLineLength(self, rpfn, funcInfo, lines):
        # check all line lengths
        fileSize = len(lines)
        fn = os.path.split(rpfn)[1]
        lineLimit = self.projFile.metrics[PF.eMetricLine]

        # get the filename and start/end line numbers
        data = {}
        for i in funcInfo:
            start = funcInfo[i]['start']
            end = funcInfo[i]['end']
            data[(start,end)] = i

        for lineNumber in range(0,fileSize):
            txt = lines[lineNumber].rstrip()
            lineLen = len(txt)
            u4cLine = lineNumber + 1 # U4C refs start at line 1

            func = 'N/A'
            for ds,de in data:
                if u4cLine >= ds and u4cLine <= de:
                    func = data[(ds,de)]

            if lineLen > lineLimit:
                severity = 'Error'
                violationId = 'Metric-Line'
                desc = 'Line Length in %s line %d' % (fn, lineNumber)
                details = '%3d: %s' % (lineLen, txt.strip())
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                                 details, u4cLine, 'U4C', self.updateTime)
        self.vDb.Commit()

    #-----------------------------------------------------------------------------------------------
    def FormatChecks(self):
        self.SetStatusMsg( msg = 'Format Checks')

    #-----------------------------------------------------------------------------------------------
    def NamingChecks(self):
        self.SetStatusMsg( msg = 'Naming Checks')

    #-----------------------------------------------------------------------------------------------
    def LanguageRestriction(self):
        # excluded functions
        # restricted functions
        self.SetStatusMsg( msg = 'Language Restrictions')

        print ('Thread A', os.getpid())
        xFuncs = self.projFile.exclude[PF.eExcludeFunc]
        xKeyword  = self.projFile.exclude[PF.eExcludeKeywords]
        rFunc = self.projFile.restricted[PF.eRestrictedFunc]
        totalItems = len(xFuncs + xKeyword + rFunc)
        counter = 1

        # identify references to excluded functions
        for item in xFuncs:
            print(item)
            counter += 1
            pct = (float(counter)/totalItems) * 100.0

            self.SetStatusMsg( pct)
            itemRefs = self.udb.LookupItem( item, 'Function')
            self.ReportExcluded( item, itemRefs, 'Error', 'Excluded-Func', 'Excluded function %s at line %d')

        # excluded key words
        for item in xKeyword:
            counter += 1
            pct = (float(counter)/totalItems) * 100.0

            self.SetStatusMsg( pct)
            itemRefs = self.udb.LookupItem( item)
            self.ReportExcluded( item, itemRefs, 'Error', 'Excluded-Keyword', 'Excluded keyword %s at line %d')

        # restricted functions
        for item in rFunc:
            counter += 1
            pct = (float(counter)/totalItems) * 100.0
            self.SetStatusMsg( pct)
            itemRefs = self.udb.LookupItem( item, 'Function')
            self.ReportExcluded( item, itemRefs, 'Warning', 'Restricted-Func', 'Restricted function %s at line %d')

    #-----------------------------------------------------------------------------------------------
    def ReportExcluded( self, item, itemRefs, severity, violationId, descFmt):
        """ This is a common reporintg function for excluded functions/keywords and restricited
            functions
        """
        for ref in itemRefs:
            print( item, ref.file(), ref.line())
            u4cLine = ref.line()
            refFunc, info = self.udb.InFunction( ref.file().longname(), u4cLine)
            fpfn = info.get('fullPath', '')
            rpfn, title = self.projFile.RelativePathName( fpfn)
            desc = descFmt % (item, u4cLine)
            details = self.ReadLineN( fpfn, u4cLine).strip()
            self.vDb.Insert( rpfn, refFunc, severity, violationId, desc,
                             details, u4cLine, 'U4C', self.updateTime)

    #-----------------------------------------------------------------------------------------------
    def ReadLineN( self, filename, lineNumber):
        """ return the text of 'lineNumber' in file 'filename'
        """
        fullPathName = self.projFile.FullPathName( filename)
        # TODO: handle non-unique filenames in different srcRoots
        f = open( fullPathName[0], 'r')
        lines = f.readlines()
        f.close()
        txt = lines[lineNumber - 1]
        return txt



