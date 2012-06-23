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
import datetime
import os
import re

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------
import understand

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
import ProjFile as PF
import ViolationDb as VDB

from tools.u4c import u4cDbWrapper as udb
from tools.u4c import U4cFileTemplates
from tools.ToolMgr import ToolSetup, ToolManager
from utils.DateTime import DateTime

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eDbDetectId = 'U4C'

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
    def __init__(self, projFile, verbose=False):
        assert( isinstance( projFile, PF.ProjectFile))

        self.projFile = projFile
        self.projRoot = projFile.paths[PF.ePathProject]

        ToolManager.__init__(self, projFile, eDbDetectId)

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
        print ('Thread %s' % eDbDetectId, os.getpid())

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
        self.SetStatusMsg( 100, msg = '%s Processing Complete' % eDbDetectId)

    #-----------------------------------------------------------------------------------------------
    def SpecializedLoad(self):
        """ This function is responsible for loading the violations into the violation DB

            This function should be run as a thread by the caller because this will allow
            the caller to report on the status of the DB Load as it runs. (i.e., % complete)
        """
        # now run the review of the u4c DB which is the other half of this process
        # get the file list to check
        self.SetStatusMsg( msg = 'Open %s DB' % eDbDetectId)
        srcRoots = self.projFile.paths[PF.ePathSrcRoot]
        excludeDirs = self.projFile.exclude[PF.eExcludeDirs]
        excludeFiles = self.projFile.exclude[PF.eExcludeU4c]
        x, srcFiles = self.projFile.GetSrcCodeFiles(srcRoots, ['.h','.c'],
                                                    excludeDirs, excludeFiles)

        # exclude all files that reside in libraryr directories
        self.srcFiles = [i for i in srcFiles if not self.projFile.IsLibraryFile(i)]

        self.updateTime = datetime.datetime.today()

        self.SetStatusMsg( msg = 'Open %s DB' % eDbDetectId)
        self.udb = udb.U4cDb( self.dbName)

        self.SetStatusMsg( msg = 'Acquire DB Lock')
        try:
            self.projFile.dbLock.acquire()

            self.CheckMetrics()
            self.CheckNaming()
            self.CheckLanguageRestrictions()
            self.CheckFormats()
            self.CheckBaseTypes()

            self.insertDeleted = self.vDb.MarkNotReported( self.toolName, self.updateTime)
            self.unanalyzed = self.vDb.Unanalyzed( self.toolName)

        except:
            raise
        finally:
            self.projFile.dbLock.release()

    #-----------------------------------------------------------------------------------------------
    def CheckMetrics(self):
        """ This function verifies all of the length limits are met on a file by fail basis.
        """
        self.SetStatusMsg( msg = 'Metric Checks')
        fileLimit = self.projFile.metrics[PF.eMetricFile]

        pctCtr = 0
        totalFiles = len(self.srcFiles)
        for i in self.srcFiles:
            pctCtr += 1
            self.SetStatusMsg( (pctCtr/float(totalFiles)*100))

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
                                details, line, eDbDetectId, self.updateTime)
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
                severity = 'Warning'
                violationId = 'Metric-Line'
                desc = 'Line Length in %s line %d' % (fn, lineNumber)
                details = '%3d: %s' % (lineLen, txt.strip())
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                                 details, u4cLine, eDbDetectId, self.updateTime)

            # check for TO-DO or T.B.D.
            txtl = txt.lower()
            todoRe = re.compile( r' ?todo[: ]+')
            tbdRe = re.compile( r' ?tbd[: ]+')
            if todoRe.search( txtl) or tbdRe.search(txtl):
                severity = 'Info'
                violationId = 'Misc-TODO'
                desc = 'Line contains TODO/TBD %s line %d' % (fn, lineNumber)
                details = '%s' % (txt.strip())
                self.vDb.Insert( rpfn, func, severity, violationId, desc,
                                 details, u4cLine, eDbDetectId, self.updateTime)

            # check for tabs
            if txt.find('\t') != -1:
                if txt.lower().find('todo') != -1 or txt.lower().find('tbd') != -1:
                    severity = 'Warning'
                    violationId = 'Misc-TAB'
                    desc = 'Line contains TAB(s) %s line %d' % (fn, lineNumber)
                    details = '%s' % (txt.strip())
                    self.vDb.Insert( rpfn, func, severity, violationId, desc,
                                     details, u4cLine, eDbDetectId, self.updateTime)

        self.vDb.Commit()

    #-----------------------------------------------------------------------------------------------
    def CheckNaming(self):
        """ Perform naming checks for all supplied item types
        """
        x = 0
        self.SetStatusMsg( msg = 'Naming Checks')

        size, fmt = self.projFile.naming[PF.eNameVar]
        varRe = re.compile( fmt)
        theItems = self.udb.db.lookup( re.compile(r'.*'), 'Object')
        self.NamingChecker( varRe, size, theItems, 'Var', 'Variable', self.GetFuncVarName)

        size, fmt = self.projFile.naming[PF.eNameFunc]
        funcRe  = re.compile( fmt)
        theItems = self.udb.db.lookup( re.compile(r'.*'), 'Function')
        self.NamingChecker( funcRe, size, theItems, 'Func', 'Function', self.GetFuncFuncName)

        size, fmt = self.projFile.naming[PF.eNameDef]
        macRe  = re.compile( fmt)
        theItems = self.udb.db.lookup( re.compile(r'.*'), 'Macro')
        self.NamingChecker( macRe, size, theItems, 'Def', 'Define', self.GetFuncVarName)

        size, fmt = self.projFile.naming[PF.eNameEnum]
        enumRe  = re.compile( fmt)
        theItems = self.udb.db.lookup( re.compile(r'.*'), 'Enumerator')
        self.NamingChecker( enumRe, size, theItems, 'Enum', 'Enum', self.GetFuncVarName)


    #-----------------------------------------------------------------------------------------------
    def NamingChecker( self, theRe, maxLength, theItems, name, longname, getFunc):
        """ Verify all variable names - global, local, static global/local """

        # Check all the vairable names
        totalItems = len(theItems)

        good = 0
        bad = 0
        badNr = 0
        libItem = 0
        pctCtr = 0

        self.SetStatusMsg(msg = 'Check %s Naming %d' % (longname, totalItems))
        for item in theItems:
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
                    # TODO: remove is U4C responds why they don't see the definition
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
                        print('CheckBadNr %s - %s' % (name, item.name()))
                else:
                    good += 1
            else:
                libItem += 1
                print('CheckLib %s - %s' % (name, item.name()))

        print('%s Good/Bad(BadNr)/libItem: %d/%d(%d)/%d' % (name,good,bad,badNr,libItem))

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
    def CheckLanguageRestrictions(self):
        """ Perform checks that restrict the usage of language elements """
        # excluded functions
        # restricted functions
        self.SetStatusMsg( msg = 'Language Restrictions')

        specialProcessing = {'register': self.HandleRegister, }

        print ('Thread A', os.getpid())

        xFuncs = self.projFile.exclude[PF.eExcludeFunc]
        xKeyword  = self.projFile.exclude[PF.eExcludeKeywords]
        rFunc = self.projFile.restricted[PF.eRestrictedFunc]

        totalItems = len(xFuncs + xKeyword + rFunc) + 1
        pctCtr = 0

        # excluded functions
        for item in xFuncs:
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
    def CheckFormats(self):
        """ Perform file/function header format checks
            This must be done last to ensure all the function info has already been filled in
        """
        self.SetStatusMsg( msg = 'Format Checks')

        self.FunctionHeaderFormat()



    #-----------------------------------------------------------------------------------------------
    def FunctionHeaderFormat(self):
        """ Verify the function header format and content
            keywords:
                <TheFunctionName> matches the current functions name
                <TheParameters> names of parameters must match, void matches empty string
                <TheReturnType> names the return type, void matches empty string

        """
        self.SetStatusMsg( msg = 'Check Function Header Format')

        # index into description indexes
        keywordRefs = {
            '<TheParameters>':-1,
            '<TheReturnType>':-1
        }

        # in the function header we look for important items
        fhDesc = self.projFile.formats[PF.eFmtFunction]

        expectFuncName = fhDesc.find( '<TheFunctionName>') != -1
        expectParams = fhDesc.find( '<TheParameters>') != -1
        expectReturn = fhDesc.find( '<TheReturnType>') != -1

        fhDescLines = fhDesc.split('\n')

        # find position of keywords in the description items
        for lx,l in enumerate(fhDescLines):
            for k in keywordRefs:
                # only collect the first instance of the keyword
                if l.find(k) != -1 and keywordRefs[k] == -1:
                    keywordRefs[k] = lx
                    if k == '<TheParameters>':
                        fhDescLines[lx] = l.replace('<TheParameters>','')
                    elif k == '<TheReturnType>':
                        fhDescLines[lx] = l.replace('<TheReturnType>', r'(?P<rtn>.*)' )

        pctCtr = 0
        totalFiles = len(self.srcFiles)
        for i in self.srcFiles:
            pctCtr += 1
            self.SetStatusMsg( (pctCtr/float(totalFiles)*100))

            # compute the relative path from a srcRoot
            rpfn, fn = self.projFile.RelativePathName( i)

            # Get file/function information
            funcInfo = self.udb.GetFileFunctionInfo( fn)

            for func in funcInfo:
                # keep the location each item is found at
                fhIndex = [-1] * len(fhDescLines)

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
                else:
                    # No functin header
                    severity = 'Error'
                    violationId = 'FuncHdr-Missing'
                    desc = 'Function Header %s is missing' % (func)
                    details = 'N/A'
                    self.vDb.Insert(rpfn, func, severity, violationId, desc,
                                    details, lineNum, eDbDetectId, self.updateTime)
                    continue

                # now scan for the description items in the Function header
                rtnText = ''
                for iix, ii in enumerate(fhDescLines):
                    ii = ii.replace( '<TheFunctionName>', '')

                    fhre = re.compile( ii, re.DOTALL)
                    wasFound = False
                    for lx,line in enumerate(hdrLines):
                        m = fhre.search( line)
                        if m:
                            fhIndex[iix] = lx
                            if expectReturn and iix == keywordRefs['<TheReturnType>']:
                                rtnText = m.group('rtn')
                            break

                # verify all the items where present and in the right order
                orderOk = []
                expectSeq = fhDescLines[:]
                for lx,name in enumerate(fhDescLines):
                    if fhIndex[lx] != -1:
                        orderOk.append( (lx, fhIndex[lx], name))
                    else:
                        # missing header field
                        at = expectSeq.index(name)
                        del expectSeq[at]
                        severity = 'Error'
                        violationId = 'FuncHdr-FieldMissing'
                        desc = 'Function Header %s missing %s' % (func, name)
                        details = 'Function header consists of %d lines' % len(hdrLines)
                        self.vDb.Insert(rpfn, func, severity, violationId, desc,
                                        details, lineNum, eDbDetectId, self.updateTime)

                # report items out of sequence in the header
                orderOk.sort( key=lambda x: x[1])
                itemSeq0 = [name for exp, act, name in orderOk]
                itemSeq = itemSeq0[:]
                for ix, item in enumerate(expectSeq):
                    if itemSeq and item != itemSeq[0]:
                        ax = itemSeq.index( item)
                        del itemSeq[ax]
                        # header field order
                        severity = 'Error'
                        violationId = 'FuncHdr-Seq'
                        desc = 'Function Header %s Info Sequence Error' % (func)
                        ax0 = itemSeq0.index( item)
                        details = '%s expected position %d found at position %d' % (item,
                                                                                    ix,
                                                                                    ax0)
                        self.vDb.Insert(rpfn, func, severity, violationId, desc,
                                        details, lineNum, eDbDetectId, self.updateTime)
                    else:
                        itemSeq = itemSeq[1:]

                # is the function name supposed to be in the header?
                if expectFuncName and hdr and hdr.find( func) == -1:
                    severity = 'Error'
                    violationId = 'FuncHdr-FuncName'
                    desc = 'Function Name %s Missing in header' % func
                    details = 'Function header consists of %d lines' % len(hdrLines)
                    self.vDb.Insert(rpfn, func, severity, violationId, desc,
                                    details, lineNum, eDbDetectId, self.updateTime)

                # check parameters - if requested and there are any
                if expectParams and params:
                    paramsAt = keywordRefs['<TheParameters>']
                    start = fhIndex[paramsAt]
                    end = fhIndex[paramsAt+1:]
                    if end:
                        paramLines = hdrLines[start:end[0]]
                    else:
                        paramLines = hdrLines[start:]

                    for px,p in enumerate(params):
                        pd = [i for i in paramLines if i.find(p) != -1]
                        if not pd:
                            severity = 'Error'
                            violationId = 'FuncHdr-Param'
                            desc = 'Function Header %s Missing Param %s' % (func, p)
                            details = 'Parameter <%s> not in description' % p
                            self.vDb.Insert(rpfn, func, severity, violationId, desc,
                                            details, lineNum, eDbDetectId, self.updateTime)

                # check return type - if requested
                if expectReturn and not rtnText and fi[udb.eFiReturnType] != 'void':
                    severity = 'Error'
                    violationId = 'FuncHdr-Return'
                    desc = 'Function Header %s Missing return info' % (func)
                    details = 'Function header consists of %d lines' % len(hdrLines)
                    self.vDb.Insert(rpfn, func, severity, violationId, desc,
                                    details, lineNum, eDbDetectId, self.updateTime)

        self.vDb.Commit()


    #-----------------------------------------------------------------------------------------------
    def FileFormat( self):
        for f in self.srcFiles:
            # detemrine file type c/h
            ext = os.path.splitext( fpfn)[1]
            if ext == '.h':
                fmt = re.compile( self.projFile.formats[PF.eFmtFile_h])

                m = fmtRe.match( 'a')





    #-----------------------------------------------------------------------------------------------
    def CheckBaseTypes( self):
        """ insure that all variables and structure definitions, return types, etc. are based on
            the project base types
            This additionally accepts: void and void*
        """
        baseTypes = self.projFile.baseTypes + ['void']
        allObjs = sorted(self.udb.db.ents( 'object'),key= lambda ent: ent.name().lower())
        totalObjs = len(allObjs)

        objStats = {'ok':0, 'bad':0, 'other':0}

        pctCtr = 0
        self.SetStatusMsg(msg = 'Check Base Types')
        letter0 = None
        for obj in allObjs:
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
                        # remove array size
                        lsq = oType.find('[')
                        rsq = oType.find(']')
                        while lsq != -1 and rsq != -1:
                            extractStr = oType[lsq:rsq+1]
                            oType = oType.replace(extractStr,'')
                            lsq = oType.find('[')
                            rsq = oType.find(']')

                        for ci in ['*', '[]', '()', 'const', 'volatile']:
                            oType = oType.replace(ci,'')

                        oType = oType.strip()
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
                    print( '%s: Type(%s), Kind(%s)' % (obj.name(), oType, obj.kindname()))
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
                    print('BaseType: Library variable %s' % obj.name())

            else:
                objStats['ok'] += 1

        print('ObjStats: ok(%d), bad(%d), other(%d)' % (objStats['ok'], objStats['bad'], objStats['other']))

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




