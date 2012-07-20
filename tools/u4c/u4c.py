"""
SciTool Understand for C/C++ Tool Manager

Design Assumptions:

Format Specification:
The user can specify the keywords they want for substitution in the format definitons by
enclosing the token in <> brackets and providing a regular expression.

"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
from collections import OrderedDict

import copy
import datetime
import os
import re
import subprocess

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------
import understand

from PySide.QtCore import *

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
from FormatChecker import FormatChecker
from tools.u4c import u4cDbWrapper as udb
from tools.u4c import U4cFileTemplates
from tools.ToolMgr import ToolSetup, ToolManager
from utils.DateTime import DateTime

import ProjFile as PF
import ViolationDb as VDB

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eDbDetectId = 'Knowlogic'

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

        toolExe = self.projFile.paths[PF.ePathU4c]

        cmdFilePath = os.path.join( self.projToolRoot, eU4cCmdFileName)

        excludeDirs = self.projFile.exclude['Dirs']
        excludeFiles = self.projFile.exclude['Files_U4c']
        incDirs, srcFiles = self.projFile.GetSrcCodeFiles( ['.c','.h'], excludeDirs, excludeFiles)

        # U4c Option definitions
        options = OrderedDict()
        options['C++Includes'] = incDirs + self.projFile.paths['IncludeDirs']
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
                optionList.append('settings -%s "%s"' % ( option+add, item))
            optionList.append('')

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
    def __init__(self, projFile, isToolRun=False):
        assert( isinstance( projFile, PF.ProjectFile))

        self.projFile = projFile
        self.projRoot = projFile.paths[PF.ePathProject]

        self.projToolRoot = os.path.join( self.projRoot, eToolRoot)

        ToolManager.__init__(self, projFile, eDbDetectId, self.projToolRoot, isToolRun)

        self.dbName = os.path.join( self.projToolRoot, eDbName)

        # this holds all the file/function info data
        self.fileFuncInfo = {}
        # this holds keyword data info by file
        self.fileKeywordData = {}

    #-----------------------------------------------------------------------------------------------
    def IsReadyToAnalyze(self, kill=False):
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
            if kill:
                self.KillU4c()

        return status

    #-----------------------------------------------------------------------------------------------
    def KillU4c(self):
        proc = subprocess.Popen( 'taskkill /im understand.exe /f')
        proc.wait()

    #-----------------------------------------------------------------------------------------------
    def RunToolAsProcess(self):
        """ This function runs a thrid party tool as a process to update any data generated
            by the third party tool.

            This function should be run as a thread by the caller becuase this will allow
            the caller to report on the status of the process as it runs. (i.e., % complete)
        """
        #self.Log ('Thread %s' % eDbDetectId, os.getpid())

        # Run the PC-Lint bat file
        self.jobCmd = '%s' % os.path.join( self.projToolRoot, eBatchName)
        ToolManager.RunToolAsProcess(self)

        fileCount = 0
        fileList = []
        analyzing = False
        self.SetStatusMsg( msg = 'Parsing Source Files')
        while self.AnalyzeActive():
            for line in self.toolProcess.stdout:
                line = line.decode(encoding='windows-1252').strip()
                self.Log( '<%s>' % line)
                self.LogFlush()
                if line == 'Analyze':
                    analyzing = True
                    fileCount = len( fileList)
                elif line.find( 'File: ') != -1:
                    line = line.replace('File: ', '').replace(' has been added.', '')
                    # add the .c files so we can track the analysis
                    if os.path.splitext( line)[1] == '.c':
                        fileList.append(line)
                elif analyzing:
                    if line in fileList:
                        fileList.remove( line)
                        v = 100 - (len(fileList)/float(fileCount)*100.0)
                        self.SetStatusMsg( v)

        self.SetStatusMsg( 100)
        self.Sleep()

        self.LoadViolations()

        parseOk = line == "Analyze Completed (Errors:0 Warnings:0)"
        openOk = self.udb.isOpen

        if parseOk and openOk:
            self.SetStatusMsg(100, 'Processing Complete')
        elif openOk:
            # if we could not open it the reason is in the status so leave it.
            self.SetStatusMsg(100, 'Processing Error Occurred - see Log File')

    #-----------------------------------------------------------------------------------------------
    def SpecializedLoad(self):
        """ This function is responsible for loading the violations into the violation DB
            NOTE: This function should be run as a thread by the caller because this will allow
            the caller to report on the status of the DB Load as it runs. (i.e., % complete)
        """
        # now run the review of the u4c DB which is the other half of this process
        # get the file list to check
        self.SetStatusMsg( msg = 'Open %s DB' % eDbDetectId)

        excludeDirs = self.projFile.exclude[PF.eExcludeDirs]
        excludeFiles = self.projFile.exclude[PF.eExcludeU4c]
        x, srcFiles = self.projFile.GetSrcCodeFiles( ['.h','.c'], excludeDirs, excludeFiles)

        # exclude all files that reside in library directories
        self.srcFiles = [i for i in srcFiles if not self.projFile.IsLibraryFile(i)]

        self.updateTime = datetime.datetime.today()

        self.SetStatusMsg( msg = 'Open %s DB' % eDbDetectId)
        self.Sleep()

        self.udb = udb.U4cDb( self.dbName)
        if not self.udb.isOpen:
            self.KillU4c()
            self.udb = udb.U4cDb( self.dbName)

        if self.udb.isOpen:
            self.SetStatusMsg( msg = 'Acquire DB Lock')
            try:
                self.projFile.dbLock.acquire()

                tasks = (
                    self.CheckMetrics,
                    self.CheckNaming,
                    self.CheckLanguageRestrictions,
                    self.CheckFormats,
                    self.CheckBaseTypes
                    )

                step = 1
                totalTasks = len( tasks)
                for t in tasks:
                    t(step,totalTasks)
                    step += 1

                    if self.abortRequest:
                        break

                if not self.abortRequest:
                    self.insertDeleted = self.vDb.MarkNotReported( self.toolName, self.updateTime)
                    self.unanalyzed = self.vDb.Unanalyzed( self.toolName)

            except:
                raise
            finally:
                self.projFile.dbLock.release()
                pass
        else:
            self.SetStatusMsg( 100, msg = 'Processing Error (see Log)\nU4C DB Open Error: %s' % self.udb.status)

    #-----------------------------------------------------------------------------------------------
    def CheckMetrics(self,step,totalTasks):
        """ This function verifies all of the length limits are met on a file by fail basis.
        """
        self.SetStatusMsg( msg = 'Metrics/File Format Checks [Step %d of %d]'%(step,totalTasks))
        fileLimit = self.projFile.metrics[PF.eMetricFile]

        pctCtr = 0
        totalFiles = len(self.srcFiles)
        for fpfn in self.srcFiles:
            if self.abortRequest:
                break

            pctCtr += 1
            self.SetStatusMsg( (pctCtr/float(totalFiles)*100))

            # compute the relative path from a srcRoot
            rpfn, fn = self.projFile.RelativePathName( fpfn)

            # Get file/function information
            funcInfo = self.udb.GetFileFunctionInfo( fn)
            func = 'N/A'

            lines = self.projFile.GetFileContents(fpfn)

            if fn == 'AircraftConfigMgr.h':
                pass

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
                                details, line, eDbDetectId, self.updateTime)
                self.vDb.Commit()

            # check the file structure against the specified layout
            #self.CheckFileFormat( fpfn, lines)
            # check the function metrics
            self.CheckFunctionMetrics( rpfn, funcInfo)

            # check the length of each line
            self.CheckLine( rpfn, funcInfo, lines)

    #-----------------------------------------------------------------------------------------------
    def CheckFunctionMetrics(self, rpfn, funcInfo):
        """ Check all the function metrics
        1. Line count
        2. Cyclomatic
        3. Max Nesting
        4. returns
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
                    details, u4cLine, eDbDetectId, self.updateTime)

            mccabe = info['metrics']['Cyclomatic']
            if mccabe > mccabeLimit:
                violationId = 'Metric-Cyclomatic'
                desc = 'Function Cyclomatic Complexity exceeded in %s' % (func)
                details = 'Cyclomatic Complexity %d exceeds %d' % (mccabe, mccabeLimit)
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                    details, u4cLine, eDbDetectId, self.updateTime)

            nesting = info['metrics']['MaxNesting']
            if nesting > nestingLimit:
                violationId = 'Metric-Nesting'
                desc = 'Function Nesting exceeded in %s' % (func)
                details = 'Nesting Levels %d exceeds %d' % (nesting, nestingLimit)
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                    details, u4cLine, eDbDetectId, self.updateTime)

            returns = info['returns']
            if returns > returnLimit:
                violationId = 'Metric-Returns'
                desc = 'Function Return Points exceeded in %s' % (func)
                details = 'Return Points %d exceeds %d' % (returns, returnLimit)
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                    details, u4cLine, eDbDetectId, self.updateTime)

        self.vDb.Commit()

    #-----------------------------------------------------------------------------------------------
    def CheckLine(self, rpfn, funcInfo, lines):
        """ Analyze for:
        1. Lines exceed the max line length
        2. Lines with the word TODO, TBD
        3. No tabs in the file
        report the line number(s) for the above
        """
        # File Specific keywords
        eFileName = '<TheFileName>'
        eTheDescription = '<TheDescription>'
        # leave these - PCLint should report these may need to do some work on it
        eLocalFuncProto = '<TheLocalFunctionPrototypes>'
        eLocalFunctions = '<TheLocalFunctions>'
        eGlobalFunctions = '<TheGlobalFunctions>'

        # check all line lengths
        fileSize = len(lines)
        fn = os.path.split(rpfn)[1]
        lineLimit = self.projFile.metrics[PF.eMetricLine]

        # get the filename and start/end line numbers
        data = {}
        for func in funcInfo:
            start = funcInfo[func]['start']
            end = funcInfo[func]['end']
            data[(start,end)] = func

        #--------------------------------- init the file format check
        # determine file type c/h
        ext = os.path.splitext( rpfn)[1]
        # build format name
        fmtName = 'File_%s' % ext.replace('.','').upper()
        fileDescLines = self.projFile.formats.get( fmtName, '')
        rawDescLines = self.projFile.rawFormats.get( fmtName, '')
        fc = FormatChecker( eDbDetectId, self.updateTime, fileDescLines, rawDescLines)

        for lx, line in enumerate( lines):
            txt = line.rstrip()
            lineLen = len(txt)
            u4cLine = lx + 1 # U4C refs start at line 1

            func = None

            # feed the file format checker
            fc.CheckLine( lx, line)

            if lineLen > lineLimit:
                func = 'N/A'
                for ds,de in data:
                    if u4cLine >= ds and u4cLine <= de:
                        func = data[(ds,de)]

                severity = 'Warning'
                violationId = 'Metric-Line'
                desc = 'Line Length in %s line %d' % (fn, lx)
                details = '%3d: %s' % (lineLen, txt.strip())
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                                 details, u4cLine, eDbDetectId, self.updateTime)

            # check for TO-DO or T.B.D.
            txtl = txt.lower()
            todoRe = re.compile( r' ?todo[: ]+')
            tbdRe = re.compile( r' ?tbd[: ]+')
            if todoRe.search( txtl) or tbdRe.search(txtl):
                if func is None:
                    func = 'N/A'
                    for ds,de in data:
                        if u4cLine >= ds and u4cLine <= de:
                            func = data[(ds,de)]
                severity = 'Info'
                violationId = 'Misc-TODO'
                desc = 'Line contains TODO/TBD %s line %d' % (fn, lx)
                details = '%s' % (txt.strip())
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                                 details, u4cLine, eDbDetectId, self.updateTime)

            # check for tabs
            if txt.find('\t') != -1:
                if txt.lower().find('todo') != -1 or txt.lower().find('tbd') != -1:
                    if func is None:
                        func = 'N/A'
                        for ds,de in data:
                            if u4cLine >= ds and u4cLine <= de:
                                func = data[(ds,de)]
                    severity = 'Error'
                    violationId = 'Misc-TAB'
                    desc = 'Line contains TAB(s) %s line %d' % (fn, lx)
                    details = '%s' % (txt.strip())
                    self.vDb.Insert( rpfn, func, severity, violationId, desc,
                                     details, u4cLine, eDbDetectId, self.updateTime)

        # check any lines remaining in the line buffer
        fc.FinishBuffer()

        #------------------------------------------------- report and file format errors
        # save this info incase we need to do some work for the three eLocal/Gloabl above
        self.fileKeywordData[rpfn] = copy.deepcopy(fc.items)
        fc.ReportErrors( self.vDb, rpfn, -1, 'File Format', rpfn, 'FileFmt')

        # check for the filename being were it is supposed to be
        keyItems = fc.GetKeywordItems( eFileName)
        if keyItems:
            for item in keyItems:
                keyInfo = item.keywords[eFileName]
                text = '\n'.join(keyInfo.lines)
                if text.lower().find( fn.lower()) == -1:
                    # no mention of file name
                    severity = 'Error'
                    violationId = 'FileFmt-FileName'
                    func = 'N/A'
                    desc = 'Missing Filename near line %d' % keyInfo.line0
                    details = 'Expected filename at line %d' % keyInfo.line0
                    self.vDb.Insert( rpfn, func, severity, violationId,
                                     desc, details, keyInfo.line0, eDbDetectId, self.updateTime)

        # check for a file description
        keyItems = fc.GetKeywordItems( eTheDescription)
        if keyItems:
            for item in keyItems:
                keyInfo = item.keywords[eTheDescription]
                text = '\n'.join(keyInfo.lines)
                rawText = item.JoinRaw()
                replaceTxt = rawText.replace( eTheDescription, '').strip()
                text = text.replace( replaceTxt, '').strip()
                if not text:
                    # no mention of file name
                    severity = 'Error'
                    violationId = 'FileFmt-NoDesc'
                    func = 'N/A'
                    desc = 'Missing File Desc near line %d' % keyInfo.line0
                    details = 'Expected file description at line %d' % keyInfo.line0
                    self.vDb.Insert( rpfn, func, severity, violationId,
                                     desc, details, keyInfo.line0, eDbDetectId, self.updateTime)

        self.vDb.Commit()

    #-----------------------------------------------------------------------------------------------
    def CheckNaming(self,step,totalTasks):
        """ Perform naming checks for all supplied item types
        """
        x = 0
        self.SetStatusMsg( msg = 'Naming Checks [Step %d of %d]'%(step,totalTasks))

        size, fmt = self.projFile.naming[PF.eNameVar]
        varRe = re.compile( fmt)
        theItems = self.udb.db.lookup( re.compile(r'.*'), 'Object')
        self.NamingChecker( step, totalTasks, varRe, size, theItems,
                            'Var', 'Variable', self.GetFuncVarName)

        size, fmt = self.projFile.naming[PF.eNameFunc]
        funcRe  = re.compile( fmt)
        theItems = self.udb.db.lookup( re.compile(r'.*'), 'Function')
        self.NamingChecker( step+0.25, totalTasks, funcRe, size, theItems,
                            'Func', 'Function', self.GetFuncFuncName)

        size, fmt = self.projFile.naming[PF.eNameDef]
        macRe  = re.compile( fmt)
        theItems = self.udb.db.lookup( re.compile(r'.*'), 'Macro')
        self.NamingChecker( step+0.25, totalTasks, macRe, size, theItems,
                            'Def', 'Define', self.GetFuncVarName)

        size, fmt = self.projFile.naming[PF.eNameEnum]
        enumRe  = re.compile( fmt)
        theItems = self.udb.db.lookup( re.compile(r'.*'), 'Enumerator')
        self.NamingChecker( step+0.25, totalTasks, enumRe, size, theItems,
                            'Enum', 'Enum', self.GetFuncVarName)

    #-----------------------------------------------------------------------------------------------
    def NamingChecker( self, step, totalTasks, theRe, maxLength, theItems, name, longname, getFunc):
        """ Verify all variable names - global, local, static global/local
        match the naming regex
        """

        # Check all the vairable names
        totalItems = len(theItems)

        good = 0
        bad = 0
        badNr = 0
        libItem = 0
        pctCtr = 0

        msg = 'Check %s Naming for %d items [Step %.2f of %d]'%(longname, totalItems, step, totalTasks)
        self.SetStatusMsg(msg = msg)
        for item in theItems:
            if self.abortRequest:
                break

            pctCtr += 1
            pct = (float(pctCtr)/totalItems) * 100
            self.SetStatusMsg( pct)

            parent = item.parent()
            # don't report library file problems
            if parent and not self.projFile.IsLibraryFile( parent.longname()):
                # find out where the variable is defined and declared
                defFile, defLine = self.udb.RefAt( item)
                decFile, decLine = self.udb.RefAt( item, 'Declare')

                # log a declared but not defined variable
                if defFile == '' and decFile != '':
                    violationId = 'Undefined-%s' % (name)
                    defFile = decFile
                    defLine = decLine
                    fpfn = decFile.longname()
                    rpfn, fn = self.projFile.RelativePathName(fpfn)
                    desc = '%s not defined: %s declared at line %d' % (longname,
                                                                       item.name(),
                                                                       decLine)
                    details = self.ReadLineN( fpfn, decLine)
                    # TODO: remove if U4C responds with a fix
                    # PWC Specific
                    if details.strip().find('EXPORT') != 0:
                        self.vDb.Insert( rpfn, 'N/A', 'Error', violationId, desc,
                                         details, decLine, eDbDetectId, self.updateTime)

                match = theRe.match( item.name())
                iLen = len(item.name())
                tooBig = iLen > maxLength
                if not match or tooBig:
                    bad += 1
                    severity = 'Error'
                    violationId = 'Naming-%s' % name
                    func = getFunc( item)

                    if defFile != '':
                        fpfn = defFile.longname()
                        rpfn, fn = self.projFile.RelativePathName(fpfn)
                        dispName = '%s%s' % (item.name(), '(Len:%d)' % iLen if tooBig else '')
                        desc = '%s naming error: %s defined at line %d' % (longname,
                                                                           dispName,
                                                                           defLine)
                        details = self.ReadLineN( fpfn, defLine)
                        self.vDb.Insert( rpfn, func, severity, violationId, desc,
                                         details, defLine, eDbDetectId, self.updateTime)
                    else:
                        badNr += 1
                        self.Log('CheckBadNr %s - %s' % (name, item.name()))
                else:
                    good += 1
            else:
                libItem += 1
                self.Log('CheckLib %s - %s' % (name, item.name()))

        self.Log('%s Good/Bad(BadNr)/libItem: %d/%d(%d)/%d' % (name,good,bad,badNr,libItem))

        self.vDb.Commit()

    #-----------------------------------------------------------------------------------------------
    def GetFuncVarName(self, item):
        """ Used by Naming rules to find a function when checking variable/enum/? """
        func = 'N/A'
        parent = item.parent()
        if parent and parent.kindname().find( 'Function') != -1:
            func = parent.name()

        return func
    #-----------------------------------------------------------------------------------------------
    def GetFuncFuncName(self, item):
        """ Used by Naming rules to find the function name when checking function names """
        func = item.name()
        return func

    #-----------------------------------------------------------------------------------------------
    def CheckLanguageRestrictions(self,step,totalTasks):
        """ Perform checks that restrict the usage of language elements """
        # excluded functions
        # restricted functions
        self.SetStatusMsg( msg = 'Language Restrictions [Step %d of %d]'%(step,totalTasks))

        specialProcessing = {'register': self.HandleRegister, }

        xFuncs = self.projFile.exclude[PF.eExcludeFunc]
        xKeyword  = self.projFile.exclude[PF.eExcludeKeywords]
        rFunc = self.projFile.restricted[PF.eRestrictedFunc]

        totalItems = len(xFuncs + xKeyword + rFunc) + 1
        pctCtr = 0

        # excluded functions
        for item in xFuncs:
            if self.abortRequest:
                break

            pctCtr += 1
            pct = (float(pctCtr)/totalItems) * 100.0
            self.SetStatusMsg( pct)
            itemRefs = self.udb.GetItemRefs( item, 'Function')
            self.ReportExcluded( item, itemRefs, 'Error', 'Excluded-Func',
                                 'Excluded function %s at line %d')

        # excluded keywords
        for item in xKeyword:
            pctCtr += 1
            pct = (float(pctCtr)/totalItems) * 100.0
            self.SetStatusMsg( pct)
            if item in specialProcessing:
                itemRefs = specialProcessing[item]()
            else:
                itemRefs = self.udb.GetItemRefs( item)
            self.ReportExcluded( item, itemRefs, 'Error', 'Excluded-Keyword',
                                 'Excluded keyword %s at line %d')

        # restricted functions
        for item in rFunc:
            pctCtr += 1
            pct = (float(pctCtr)/totalItems) * 100.0
            self.SetStatusMsg( pct)
            itemRefs = self.udb.GetItemRefs( item, 'Function')
            self.ReportExcluded( item, itemRefs, 'Warning', 'Restricted-Func',
                                 'Restricted function %s at line %d')

    #-----------------------------------------------------------------------------------------------
    def HandleRegister( self):
        """ handle the declaration of a register variable if the user has disallowed this """
        # TODO: check that no local variable type is declared as a register
        return []

    #-----------------------------------------------------------------------------------------------
    def ReportExcluded( self, item, itemRefs, severity, violationId, descFmt):
        """ This is a common reporintg function for excluded functions/keywords and restricited
            functions
        """
        for ref in itemRefs:
            u4cLine = ref.line()
            fpfn = ref.file().longname()
            refFunc, info = self.udb.InFunction( fpfn, u4cLine)
            rpfn, title = self.projFile.RelativePathName( fpfn)
            desc = descFmt % (item, u4cLine)
            details = self.ReadLineN( fpfn, u4cLine).strip()
            self.vDb.Insert( rpfn, refFunc, severity, violationId, desc,
                             details, u4cLine, eDbDetectId, self.updateTime)

        if itemRefs:
            self.vDb.Commit()

    #-----------------------------------------------------------------------------------------------
    def CheckFormats(self,step,totalTasks):
        """ Perform file/function header format checks
            This must be done last to ensure all the function info has already been filled in
        """
        self.SetStatusMsg( msg = 'Format Checks [Step %d of %d]'%(step,totalTasks))

        self.FunctionHeaderFormat()

    #-----------------------------------------------------------------------------------------------
    def FunctionHeaderFormat(self):
        """ Verify the function header format and content
            keywords:
                <TheFunctionName> matches the current functions name
                <TheParameters> names of parameters must match, void matches empty string
                <TheReturnType> names the return type, void matches empty string

        """
        # Function Header Specific keywords
        eFunctionName = '<TheFunctionName>'
        eParams = '<TheParameters>'
        eParamsIn = '<TheParametersIn>'
        eParamsOut = '<TheParametersOut>'
        eParamsInOut = '<TheParametersInOut>'
        eReturnType = '<TheReturnType>'

        self.SetStatusMsg( msg = 'Check Function Header Format')

        # in the function header we look for important items
        fhDesc = self.projFile.formats[PF.eFmtFunction]
        fhRawDesc = self.projFile.rawFormats[PF.eFmtFunction]

        fc = FormatChecker( eDbDetectId, self.updateTime, fhDesc, fhRawDesc)

        pctCtr = 0
        totalFiles = len(self.srcFiles)
        for i in self.srcFiles:
            if self.abortRequest:
                break

            pctCtr += 1
            self.SetStatusMsg( (pctCtr/float(totalFiles)*100))

            # compute the relative path from a srcRoot
            rpfn, fn = self.projFile.RelativePathName( i)

            # Get file/function information
            funcInfo = self.udb.GetFileFunctionInfo( fn)

            for func in funcInfo:
                if func == 'ConvertToDegC':
                    pass

                # get function info
                fi = funcInfo[func]
                hdr = fi[udb.eFiHeader]
                params = fi[udb.eFiParams]
                lineNum = fi[udb.eFiStart]

                # header split by line
                if hdr:
                    hdrLines = hdr.split('\n')
                    fc.Check(hdr)
                    fc.ReportErrors( self.vDb, rpfn, lineNum, 'Function Header',
                                     func, 'FuncHdr')
                else:
                    # No function header
                    severity = 'Error'
                    violationId = 'FuncHdr-Missing'
                    desc = 'Function Header %s is missing' % (func)
                    details = 'N/A'
                    self.vDb.Insert(rpfn, func, severity, violationId, desc,
                                    details, lineNum, eDbDetectId, self.updateTime)
                    continue

                # is the function name supposed to be in the header?
                keyItems = fc.GetKeywordItems(eFunctionName)
                if keyItems:
                    for item in keyItems:
                        keyInfo = item.keywords[eFunctionName]
                        searchIn = '\n'.join(keyInfo.lines)
                        if searchIn.find( func) == -1:
                            severity = 'Error'
                            violationId = 'FuncHdr-FuncName'
                            desc = 'Function Name %s Missing in header' % func
                            details = 'Expected at offset %d of %d lines' % (keyInfo.line0, len(hdrLines))
                            self.vDb.Insert(rpfn, func, severity, violationId, desc,
                                            details, lineNum, eDbDetectId, self.updateTime)

                # check parameters - if requested and collect associated lines
                # TODO: detect actual out param types *, & report misplaced comments
                expectParams = False
                paramLines = []
                for p in (eParams, eParamsIn, eParamsOut, eParamsInOut):
                    keyItems = fc.GetKeywordItems(p)
                    for item in keyItems:
                        expectParams = True
                        paramLines.extend( item.keywords[p].lines)

                # collect any lines associated with parameters and see if all the params are defined
                if expectParams:
                    searchIn = '\n'.join( paramLines)
                    for px,p in enumerate(params):
                        if searchIn.find( p) == -1:
                            severity = 'Error'
                            violationId = 'FuncHdr-Param'
                            desc = 'Function Header %s Missing Param %s' % (func, p)
                            details = 'Parameter <%s> not in description' % p
                            self.vDb.Insert(rpfn, func, severity, violationId, desc,
                                            details, lineNum, eDbDetectId, self.updateTime)

                # check return type - if requested
                keyItems = fc.GetKeywordItems(eReturnType)
                for item in keyItems:
                    searchIn = '\n'.join(item.keywords[eReturnType].lines)
                    rawText = item.JoinRaw()
                    rtnLineDesc = rawText.replace(eReturnType, '')
                    searchIn = searchIn.replace( rtnLineDesc, '').strip()
                    if not searchIn and fi[udb.eFiReturnType] != 'void':
                        severity = 'Error'
                        violationId = 'FuncHdr-Return'
                        desc = 'Function Header %s Missing return info' % (func)
                        details = 'Function header consists of %d lines' % len(hdrLines)
                        self.vDb.Insert(rpfn, func, severity, violationId, desc,
                                        details, lineNum, eDbDetectId, self.updateTime)

        self.vDb.Commit()


    #-----------------------------------------------------------------------------------------------
    def CheckBaseTypes( self,step,totalTasks):
        """ insure that all variables and structure definitions, return types, etc. are based on
            the project base types
            This additionally accepts: void and void*
        """
        baseTypes = self.projFile.baseTypes + ['void']
        allObjs = sorted(self.udb.db.ents( 'object'),key= lambda ent: ent.name().lower())
        totalObjs = len(allObjs)

        objStats = {'ok':0, 'bad':0, 'other':0}

        pctCtr = 0
        self.SetStatusMsg(msg = 'Check Base Types [Step %d of %d]'%(step,totalTasks))
        letter0 = None
        for obj in allObjs:
            if self.abortRequest:
                break

            pctCtr += 1
            pct = (float(pctCtr)/totalObjs) * 100
            self.SetStatusMsg( pct)

            oType = obj.type()
            typeOk = True

            if oType not in baseTypes:
                typeOk = False
                if oType is None:
                    # make sure this is a typedef
                    if obj.kindname().lower() == 'typedef':
                        typeOk = True
                else:
                    # check is part of type is in any basetype
                    for b in baseTypes:
                        if oType.find( b) != -1:
                            typeOk = True
                            break
                    else:
                        # clean up the type
                        inOtype = oType
                        # must be 1st or escaped ']' and '-'
                        cleanRe = re.compile(r'const|volatile|[()+\-*/]+?')
                        numRe = re.compile(r'\[[0-9A-Za-z_\- ]*\]')
                        repStr = cleanRe.findall( oType)
                        for i in repStr:
                            oType = oType.replace(i,'')

                        # remove extra numbers
                        rep1Str = numRe.findall( oType)
                        for i in rep1Str:
                            oType = oType.replace(i,'')

                        oType = oType.strip()
                        #self.Log('In: <%s> Out: <%s> RepStr: %s - %s' % (inOtype, oType,
                        #                                              str(repStr), str(rep1Str)))

                        tdefFound = self.udb.db.lookup(oType, 'Typedef')
                        tdefFound = [i for i in tdefFound if i.name() == oType]

                        if len(tdefFound) != 1:
                            objStats['bad'] += 1
                        else:
                            typeOk = True

            if not typeOk:
                defFile, defLine = self.udb.FindEnt( obj)
                if defFile != '':
                    objStats['bad'] += 1
                    self.Log( '%s: Type(%s), Kind(%s)' % (obj.name(), oType, obj.kindname()))
                    severity = 'Error'
                    violationId = 'BaseType'
                    fpfn = defFile.longname()
                    rpfn, title = self.projFile.RelativePathName(fpfn)
                    func, info = self.udb.InFunction( fpfn, defLine)
                    details = self.ReadLineN( fpfn, defLine)
                    desc = 'Base Type Error: %s line %d' % (obj.name(), defLine)
                    self.vDb.Insert( rpfn, func, severity, violationId, desc,
                                     details, defLine, eDbDetectId, self.updateTime)
                    if letter0 != obj.name()[0]:
                        letter0 = obj.name()[0]
                        self.vDb.Commit()
                else:
                    self.Log('BaseType: Library variable %s' % obj.name())

            else:
                objStats['ok'] += 1

        self.Log('ObjStats: ok(%d), bad(%d), other(%d)' % (objStats['ok'], objStats['bad'], objStats['other']))

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




