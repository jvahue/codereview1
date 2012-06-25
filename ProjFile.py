"""
Configuration Manager Object
This object knows how to read and write the project files for a project.
The GUI sets values based on user defintions and this object saves them to the project file, and
the GUI displays the values read from the project file

This object is the nexus for all thing project configuraiton based.  Objects call into this object
in order get the project specific values for these any item requested.

The following is a list of project configuraiton items currently support :

[Path_ProjectRoot] - the root directory for the project - this file resides there
[Path_SrcCodeRoot] - source code rott directory
[Path_IncludeDirs] - any directories that exist outside the SrcCodeRoot
[Path_PcLint] - Path to the PcLint executable
[Path_U4c] - path to U4c executable "und"
[Defines] - any defines there are two forms
    item
    item=value
[Undefines] - specific undefine values one form
    item
[Exclude_Files_PcLint] - filenames exclude from the PcLint check
[Exclude_Files_U4c] - filenames excluded from U4C analysis
[Exclude_Functions] - excluded functions that cannot appear in the code
[Exclude_Keywords] - excluded keywords
[Format_File_h] - a description of the expected header file format
[Format_File_c] - a description of the expected c file format
[Format_FunctionHeader] - a description of the expected function header
[Metrics] - metric limits see below for specifics and default values
    complexityMcCabe=10
    complexityNesting=5
    lengthFile=3000
    lengthFunction=200
    lengthLine=95
    functionReturns=1
[Naming] - naming rules for the items shown below and default values
    function=[A-Za-z0-9_]{1,32}
    variable=[A-Za-z0-9_]{132}
    enum=[A-Za-z0-9_]{1,32}
    constants=[A-Za-z0-9_]{1,32}
    defines=[A-Za-z0-9_]{1,32}
[Options_PcLint] - user defined options for PcLint
[Restricted_Functions] - restricted functions, these functions are allowed but their use is flagged

"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
from collections import OrderedDict

import copy
import inspect
import threading
import os

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
ePcLintPath = r'C:\lint\lint-nt.exe'
eU4cPath = r'C:\Program Files\SciTools\bin\pc-win64\und.exe'

ePathProject = 'ProjectRoot'
ePathSrcRoot = 'SrcCodeRoot'
ePathInclude = 'IncludeDirs'
ePathPcLint  = 'PcLint'
ePathU4c     = 'U4c'

eExcludeDirs = 'Dirs'
eExcludePcLint = 'Files_PcLint'
eExcludeU4c    = 'Files_U4c'
eExcludeFunc   = 'Functions'
eExcludeKeywords = 'Keywords'

eFmtRegex = 'Regex'
eFmtFile_h = 'File_H'
eFmtFile_c = 'File_C'
eFmtFunction = 'FunctionHeader'

eMetricMcCabe = 'complexityMcCabe'
eMetricNesting = 'complexityNesting'
eMetricFile = 'lengthFile'
eMetricLine = 'lengthLine'
eMetricFunc = 'lengthFunction'
eMetricReturns = 'functionReturns'

eNameFunc = 'function'
eNameVar  = 'variable'
eNameEnum = 'enum'
eNameConst = 'constants'
eNameDef = 'defines'

eOptPcLint = 'PcLint'
eRestrictedFunc = 'Functions'

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
class ProjectFile:
    """
    This class implements the project file for the Code Review Tool
    """
    #-----------------------------------------------------------------------------------------------
    def __init__(self, ffn):
        """ Read/Create a Project file with the specified name
        """
        self.Reset(ffn)

        if not os.path.isdir(self.paths['ProjectRoot']):
            os.makedirs( self.paths['ProjectRoot'])

        if not os.path.isfile( ffn):
            self.modified = True
            self.Save()
        else:
            self.Open()

        self.dbLock = threading.Lock()

    #-----------------------------------------------------------------------------------------------
    def Reset(self, ffn):
        """ Init/declare all the variable for this class
        """
        self.projFileName = ffn
        self.projName = os.path.splitext(os.path.split(ffn)[1])[0]

        self.paths = OrderedDict()
        self.paths[ePathProject] = os.path.split(ffn)[0]
        self.paths[ePathSrcRoot] = [] # a list of roots
        self.paths[ePathInclude] = [] # a list of include dirs
        self.paths[ePathPcLint] = ePcLintPath  # path to PcLint executable
        self.paths[ePathU4c] = eU4cPath        # path to U4c executable

        self.defines = []     # a list of defines
        self.undefines = []

        self.exclude = OrderedDict()
        self.exclude[eExcludeDirs] = []
        self.exclude[eExcludePcLint] = []
        self.exclude[eExcludeU4c] = []
        self.exclude[eExcludeFunc] = []
        self.exclude[eExcludeKeywords] = []

        self.formats = OrderedDict()
        self.formats[eFmtRegex] = OrderedDict()
        self.formats[eFmtFile_h] = ''
        self.formats[eFmtFile_c] = ''
        self.formats[eFmtFunction] = ''

        self.metrics = OrderedDict()
        self.metrics[eMetricMcCabe] = 10
        self.metrics[eMetricNesting] = 5
        self.metrics[eMetricFile] = 3000
        self.metrics[eMetricFunc] = 250
        self.metrics[eMetricLine] = 95
        self.metrics[eMetricReturns] = 1

        self.naming = OrderedDict()
        self.naming[eNameFunc] = r'[A-Za-z0-9_]{1,32}'
        self.naming[eNameVar] = r'[A-Za-z0-9_]{1,32}'
        self.naming[eNameEnum] = r'[A-Za-z0-9_]{1,32}'
        self.naming[eNameConst] = r'[A-Za-z0-9_]{1,32}'
        self.naming[eNameDef] = r'[A-Za-z0-9_]{1,32}'

        self.baseTypes = []

        self.options = OrderedDict()
        self.options[eOptPcLint] = ''

        self.restricted = OrderedDict()
        self.restricted[eRestrictedFunc] = []

        self.modified = False

    #-----------------------------------------------------------------------------------------------
    def GetSrcCodeFiles( self, extensions=['.h','.c'], excludeDirs=[], excludedFiles=[]):
        """ Walk all srcCode roots and files with extension in extensions unless
            the file is in the excludeFileList

            All .h files seen have their src directory returned in includeDirs
        """
        srcFiles = []
        includeDirs = []
        for root in self.paths[ePathSrcRoot]:
            for dirPath, dirs, fileNames in os.walk( root):
                if dirPath not in excludeDirs:
                    for f in fileNames:
                        ffn = os.path.join( dirPath, f)
                        ext = os.path.splitext( f)[1]

                        if ext == '.h' and dirPath not in includeDirs:
                            includeDirs.append( dirPath)

                        if os.path.isfile(ffn) and ext in extensions:
                            if f not in excludedFiles:
                                srcFiles.append( ffn)

        return includeDirs, srcFiles

    #-----------------------------------------------------------------------------------------------
    # Open / Read Operations
    #-----------------------------------------------------------------------------------------------
    def Open( self):
        """ Read in the contents of a project file
        """
        self.projectFile = open( self.projFileName , 'r')
        self.projectFileData = self.projectFile.readlines()
        self.projectFile.close()

        self.ReadPaths()
        self.ReadDefs()
        self.ReadExcludes()
        self.ReadFormats()
        self.ReadMetrics()
        self.ReadNaming()
        self.ReadOptions()
        self.ReadRestricted()
        self.ReadBaseTypes()

        # save the raw format info
        self.rawFormats = copy.deepcopy( self.formats)

        # replace keywords in formats
        for t in self.formats:
            if t != eFmtRegex:
                v = self.formats[t]
                # make sure '\' is done first
                for c in r'\.^$*+?{}[]|()':
                    v = v.replace(c, r'\%s' % c)
                for k in self.formats[eFmtRegex]:
                    kv = self.formats[eFmtRegex][k]
                    v = v.replace( k, kv)
                    self.formats[t] = v

    #-----------------------------------------------------------------------------------------------
    def ReadPaths( self):
        """ Write the project and src code root info to the file """
        self.paths['ProjectRoot'] = self.GetLine( 'Path_ProjectRoot')
        self.paths['SrcCodeRoot'] = self.GetList( 'Path_SrcCodeRoot')
        self.paths['IncludeDirs'] = self.GetList( 'Path_IncludeDirs')
        self.paths['PcLint'] = self.GetLine( 'Path_PcLint')
        self.paths['U4c'] = self.GetLine( 'Path_U4c')

    #-----------------------------------------------------------------------------------------------
    def ReadDefs( self):
        self.defines = self.GetList( 'Defines')
        self.undefines = self.GetList( 'Undefines')

    #-----------------------------------------------------------------------------------------------
    def ReadExcludes( self):
        for group in self.exclude:
            self.exclude[group] = self.GetList( 'Exclude_%s' % group)

    #-----------------------------------------------------------------------------------------------
    def ReadFormats( self):
        for i in self.formats:
            if i != eFmtRegex:
                self.formats[i] = self.GetMultiLines( 'Format_%s' % i)
            else:
                self.formats[i] = self.ReadDict( 'Format_%s' % i)

    #-----------------------------------------------------------------------------------------------
    def ReadMetrics( self):
        at = self.GetHdr( 'Metrics')
        if at != -1:
            at += 1
            while at < len(self.projectFileData):
                line = self.projectFileData[at]
                parts = line.strip().split('=')
                if len(parts) == 2:
                    at += 1
                    try:
                        self.metrics[parts[0].strip()] = int(parts[-1])
                    except ValueError:
                        pass
                else:
                    break

    #-----------------------------------------------------------------------------------------------
    def ReadDict( self, group):
        # TODO: assert on format error
        od = OrderedDict()
        at = self.GetHdr( group)
        if at != -1:
            at += 1
            while at < len(self.projectFileData):
                line = self.projectFileData[at]
                at += 1
                parts = line.strip().split('=')
                if len(parts) == 2:
                    name = parts[0].strip()
                    info = parts[1].strip()
                    od[name] = info
                else:
                    break

        return od

    #-----------------------------------------------------------------------------------------------
    def ReadNaming( self):
        # TODO: assert on format error
        at = self.GetHdr( 'Naming')
        if at != -1:
            at += 1
            while at < len(self.projectFileData):
                line = self.projectFileData[at]
                at += 1
                parts = line.strip().split('=')
                if len(parts) == 2:
                    info = parts[-1]
                    szFmt = info.split(':')
                    if len(szFmt) == 1:
                        sz = 32
                        fmt = szFmt[0]
                    else:
                        sz = int(szFmt[0])
                        fmt = szFmt[1]
                    self.naming[parts[0].strip()] = (sz, fmt)
                else:
                    break

    #-----------------------------------------------------------------------------------------------
    def ReadOptions( self):
        for i in self.options:
            self.options[i] = self.GetMultiLines( 'Options_%s' % i)

    #-----------------------------------------------------------------------------------------------
    def ReadBaseTypes( self):
        self.baseTypes = self.GetList( 'Base_Types')

    #-----------------------------------------------------------------------------------------------
    def ReadRestricted( self):
        for i in self.restricted:
            self.restricted[i] = self.GetList( 'Restricted_%s' % i)


    #-----------------------------------------------------------------------------------------------
    # Save / Write Operations
    #-----------------------------------------------------------------------------------------------
    def Save( self, ffn = None):
        """ Save the project file """
        if self.modified or ffn is not None:
            if ffn is None:
                ffn = self.projFileName
            self.projectFile = open( ffn, 'w')

            self.WritePaths()
            self.WriteDefs()
            self.WriteExcludes()
            self.WriteFormats()
            self.WriteMetrics()
            self.WriteNaming()
            self.WriteBaseTypes()
            self.WriteOptions()
            self.WriteRestricted()

            self.projectFile.close()

    #-----------------------------------------------------------------------------------------------
    def WritePaths( self):
        """ Write the project and src code root info to the file """
        self.PutLine( 'Path_ProjectRoot', self.paths['ProjectRoot'])
        self.PutList( 'Path_SrcCodeRoot', self.paths['SrcCodeRoot'])
        self.PutList( 'Path_IncludeDirs', self.paths['IncludeDirs'])
        self.PutLine( 'Path_PcLint', self.paths['PcLint'])
        self.PutLine( 'Path_U4c', self.paths['U4c'])

    #-----------------------------------------------------------------------------------------------
    def WriteDefs( self):
        self.PutList( 'Defines', self.defines)
        self.PutList( 'Undefines', self.undefines)

    #-----------------------------------------------------------------------------------------------
    def WriteExcludes( self):
        for group in self.exclude:
            self.PutList( 'Exclude_%s' % group, self.exclude[group])

    #-----------------------------------------------------------------------------------------------
    def WriteFormats( self):
        self.PutDictItems( 'Format', self.formats)

    #-----------------------------------------------------------------------------------------------
    def WriteMetrics( self):
        self.PutHdr( 'Metrics')
        for i in self.metrics:
            self.projectFile.write( '%s=%d\n' % (i, self.metrics[i]))

    #-----------------------------------------------------------------------------------------------
    def WriteNaming( self):
        self.PutHdr( 'Naming')
        for i in self.naming:
            self.projectFile.write( '%s=%s\n' % (i, self.naming[i]))

    #-----------------------------------------------------------------------------------------------
    def WriteBaseTypes( self):
        self.PutList( 'Base_Types', self.baseTypes)

    #-----------------------------------------------------------------------------------------------
    def WriteOptions( self):
        self.PutDictItems( 'Options', self.options)

    #-----------------------------------------------------------------------------------------------
    def WriteRestricted( self):
        self.PutDictItems( 'Restricted', self.restricted)

    #-----------------------------------------------------------------------------------------------
    # Utilities
    #-----------------------------------------------------------------------------------------------
    def GetFileContents( self, fpfn):
        lines = []
        if os.path.isfile( fpfn):
            f = open( fpfn, 'r')
            lines = f.readlines()
            f.close()
        return lines

    #-----------------------------------------------------------------------------------------------
    def GetHdr( self, header):
        at = 0
        hdr = '[%s]' % header
        while at < len(self.projectFileData) and self.projectFileData[at].find( hdr) == -1:
            at += 1

        if at >= len(self.projectFileData):
            at = -1

        return at

    #-----------------------------------------------------------------------------------------------
    def GetLine( self, header):
        """ Save a list of objects
        """
        at = self.GetHdr( header)
        if at == -1:
            return ''
        else:
            return self.projectFileData[at+1].strip()

    #-----------------------------------------------------------------------------------------------
    def GetMultiLines( self, header):
        """ Save a list of objects
        """
        data = ''
        at = self.GetHdr( header)
        if at != -1:
            data = []
            at += 1
            while at < len(self.projectFileData):
                line = self.projectFileData[at].strip()
                if not line or (line[0] != '[' and line[-1] != ']'):
                    data.append( line)
                    at += 1
                else:
                    # remove the last line as it is the prefix to the [ini] header
                    data = data[:-1]
                    break
            data = '\n'.join(data)

        return data

    #-----------------------------------------------------------------------------------------------
    def GetList( self, header):
        """ Save a list of objects
        """
        newList = []
        at = self.GetHdr( header)
        if at != -1:
            at += 1
            while at < len(self.projectFileData):
                v = self.projectFileData[at].strip()
                if v:
                    newList.append( v)
                    at += 1
                else:
                    break
        return newList

    #-----------------------------------------------------------------------------------------------
    def PutHdr( self, header):
        self.projectFile.write( '\n[%s]\n' % header)

    #-----------------------------------------------------------------------------------------------
    def PutLine( self, header, line):
        """ Save a list of objects
        """
        self.PutHdr( header)
        self.projectFile.write( '%s\n' % str(line))

    #-----------------------------------------------------------------------------------------------
    def PutList( self, header, theList):
        """ Save a list of objects
        """
        self.PutHdr( header)
        for listItem in theList:
            self.projectFile.write( '%s\n' % listItem)

    #-----------------------------------------------------------------------------------------------
    def PutDictItems( self, header, theDict):
        """ Save a dict of items
        """
        for item in theDict:
            itemHdr = '%s_%s' % (header, item)
            itemValue = theDict[item]
            if type(itemValue) == list:
                self.PutList( itemHdr, itemValue)
            else:
                self.PutLine( itemHdr, itemValue)

    #-----------------------------------------------------------------------------------------------
    def FullPathName( self, rpfn):
        """ Convert a relative path file name into a full path filename, unless
            it already is a full path name
        """
        if os.path.isfile( rpfn):
            fullPathNames = [rpfn]
        else:
            fullPathNames = []

            # see what we got
            path, title = os.path.split( rpfn)
            srcRoots = self.paths[ePathSrcRoot]

            if path:
                for i in srcRoots:
                    fpfn = os.path.join( i, rpfn)
                    if os.path.isfile( fpfn):
                        fullPathNames.append( fpfn)
            else:
                includes, names = self.GetSrcCodeFiles()
                for s in srcRoots:
                    for i in includes:
                        fpfn = os.path.join( s, i, rpfn)
                        if os.path.isfile( fpfn):
                            fullPathNames.append( fpfn)

        return fullPathNames

    #-----------------------------------------------------------------------------------------------
    def RelativePathName( self, fpfn):
        """ Convert a full path name to a relative path file name
            return: rpfn, title
        """
        relPathNames = []
        srcRoots = self.paths[ePathSrcRoot]

        # compute the relative path from a srcRoot
        for sr in srcRoots:
            fn = fpfn.replace(sr, '')
            if fn != fpfn:
                if fn[0] in ('/', '\\'):
                    fn = fn[1:]
                    break
        rpfn = fn
        fn = os.path.split(rpfn)[1]
        return rpfn, fn

    #-----------------------------------------------------------------------------------------------
    def IsLibraryFile( self, fpfn):
        """ Return true if this file is held in a include path.  These files are considered library
            files and so we have no control over them, don't report errors
        """
        isLibrary = False
        for i in self.paths[ePathInclude]:
            if fpfn.find(i) != -1:
                isLibrary = True
        return isLibrary

#===================================================================================================
if __name__ == '__main__':
    pf = r'D:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ\G4.crp'
    pf1 = r'D:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ\G41a.crp'
    pf2 = r'D:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ\G42.crp'
    pf0 = ProjectFile(pf)
    r,f = pf0.RelativePathName(r'D:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\application\FASTStateMgr.c')
    r,f = pf0.RelativePathName('')
    pf0.modified = True
    pf0.Save(pf1)