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
#import inspect
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
ePathViewer  = 'Viewer'

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

eAnalysisComments = 'Analysis_Comments'

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
        if os.name == 'nt':
            # windows machine paths are case insensitive
            self.pathCaseMatters = False
        else:
            self.pathCaseMatters = True

        self.Reset(ffn)

        if not os.path.isdir(self.paths['ProjectRoot']):
            os.makedirs( self.paths['ProjectRoot'])

        self.Open()

        self.dbLock = threading.Lock()

    #-----------------------------------------------------------------------------------------------
    def Reset(self, ffn):
        """ Init/declare all the variable for this class
        """
        self.projFileName = ffn
        self.projName = os.path.splitext(os.path.split(ffn)[1])[0]

        self.sectionTips = {}

        self.paths = OrderedDict()
        self.paths[ePathProject] = os.path.split(ffn)[0]
        self.paths[ePathSrcRoot] = [] # a list of roots
        self.paths[ePathInclude] = [] # a list of include dirs
        self.paths[ePathPcLint] = ePcLintPath # path to PcLint executable
        self.paths[ePathU4c] = eU4cPath # path to U4c executable
        self.paths[ePathViewer] = None # path/cmdline to run the viewer <filename> <linenumber>

        self.sectionTips[ePathProject] = "A single path specifying the full path to the project"

        self.sectionTips[ePathSrcRoot] = "A List of paths specifying where to find code. "
        self.sectionTips[ePathSrcRoot] += "Subdirectories below each path are included"

        self.sectionTips[ePathInclude] = "A list of include paths."
        self.sectionTips[ePathPcLint] = "The path to the PC-Lint installation"
        self.sectionTips[ePathU4c] = "The path to the Understand installation"

        self.sectionTips[ePathViewer] = "The path and command for your code viewer. "
        self.sectionTips[ePathViewer] += "If your view supports a filename and line number "
        self.sectionTips[ePathViewer] += "put the following in the command <filename> <linenumber> "
        self.sectionTips[ePathViewer] += "these will be converted by the CRT at run time. "
        self.sectionTips[ePathViewer] += "The follwing will open Understand at the specified line\n\n"
        self.sectionTips[ePathViewer] += r"<UnderstandPath>\understand.exe -visit <fullPathFileName> <lineNumber>"

        self.defines = []     # a list of defines
        self.sectionTips["Defines"] = "System Wide Defines for C/C++"

        self.undefines = []
        self.sectionTips["Undefines"] = "System Wide UnDefines for C/C++"

        self.exclude = OrderedDict()
        self.exclude[eExcludeDirs] = []
        self.exclude[eExcludePcLint] = []
        self.exclude[eExcludeU4c] = []
        self.exclude[eExcludeFunc] = []
        self.exclude[eExcludeKeywords] = []

        self.sectionTips[eExcludeDirs] = 'A List of directories to exclude from processing, '
        self.sectionTips[eExcludeDirs] += "maybe the build result directory or a test code directory."
        self.sectionTips[eExcludePcLint] = 'A list of files to exclude from PC-Lint analysis. '
        self.sectionTips[eExcludeU4c] = 'A list of files to exclude from Understand analysis .'
        self.sectionTips[eExcludeFunc] = 'A list of functions that cannot be used. '
        self.sectionTips[eExcludeKeywords] = 'A list of keywords that cannot be used.'

        self.formats = OrderedDict()
        self.formats[eFmtRegex] = OrderedDict()
        self.formats[eFmtFile_h] = ''
        self.formats[eFmtFile_c] = ''
        self.formats[eFmtFunction] = ''

        self.sectionTips[eFmtRegex] = 'A set of key/value pairs that define a regex substitution '
        self.sectionTips[eFmtRegex] += 'These keys can be placed in you description of files or '
        self.sectionTips[eFmtRegex] += 'function headers.\n\n'
        self.sectionTips[eFmtRegex] += 'For example if you expect a date in a file at a particular location '
        self.sectionTips[eFmtRegex] += 'you could create <date>=[0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{1,2} this '
        self.sectionTips[eFmtRegex] += 'can then be used any place in your description'

        self.sectionTips['Format_File'] = 'A description of a file based on items you want to see in the file, '
        self.sectionTips['Format_File'] += 'in the order you wanto to see them.  When items have a relative '
        self.sectionTips['Format_File'] += 'position to other lines in the item put a :n: at the end of the '
        self.sectionTips['Format_File'] += 'line to show it is supposed to be n lines after the prvious item. '
        self.sectionTips['Format_File'] += 'If you want to make sure you cannot find an item unless the previous '
        self.sectionTips['Format_File'] += 'item is found put a :D: at the end of the line.'

        self.sectionTips[eFmtFunction] = 'A description of the format of your function header'

        self.metrics = OrderedDict()
        self.metrics[eMetricMcCabe] = 10
        self.metrics[eMetricNesting] = 5
        self.metrics[eMetricFile] = 3000
        self.metrics[eMetricFunc] = 250
        self.metrics[eMetricLine] = 95
        self.metrics[eMetricReturns] = 1
        self.sectionTips['[Metrics]'] = 'The specific limit which cannot be exceeded in your code.'

        self.naming = OrderedDict()
        self.naming[eNameFunc] = r'[A-Za-z0-9_]{1,32}'
        self.naming[eNameVar] = r'[A-Za-z0-9_]{1,32}'
        self.naming[eNameEnum] = r'[A-Za-z0-9_]{1,32}'
        self.naming[eNameConst] = r'[A-Za-z0-9_]{1,32}'
        self.naming[eNameDef] = r'[A-Za-z0-9_]{1,32}'

        self.sectionTips['[Naming]'] = 'Regex for the items defined'

        self.baseTypes = []
        self.sectionTips['[Base_Types]'] = 'The only types for all items to be specified as.'

        self.options = OrderedDict()
        self.options[eOptPcLint] = ''
        self.sectionTips[eOptPcLint] = 'Specify all you PC-Lint options'

        self.restricted = OrderedDict()
        self.restricted[eRestrictedFunc] = []
        self.sectionTips[eRestrictedFunc] = 'Any function that has not been verified for your current installation '
        self.sectionTips[eRestrictedFunc] += 'and that has undefined behaviour by based on the language defintion.'

        self.analysisComments = []
        self.sectionTips['[Analysis_Comments]'] = 'A list of canned comments to alpply to your analysis of the tool findings.'

        self.modified = False
        self.isValid = False

        self.errors = []

    #-----------------------------------------------------------------------------------------------
    def GetTip( self, iniGroup):
        """ Get the tip associated with the iniGroup
        """
        tip = ''

        for i in self.sectionTips:
            if iniGroup.find(i) != -1:
                tip = self.sectionTips[i]
                break

        return tip

    #-----------------------------------------------------------------------------------------------
    def GetSrcCodeFiles( self, extensions=('.h','.c','.cpp','.hpp'), excludeDirs=(), excludedFiles=()):
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
    def GetErrorText( self):
        """ Walk all srcCode roots and files with extension in extensions unless
            the file is in the excludeFileList

            All .h files seen have their src directory returned in includeDirs
        """
        text = '\n'.join( self.errors)
        return text

    #-----------------------------------------------------------------------------------------------
    # Open / Read Operations
    #-----------------------------------------------------------------------------------------------
    def Open( self):
        """ Read in the contents of a project file
        """
        if os.path.isfile( self.projFileName):
            self.projectFile = open( self.projFileName , 'r')
            rawLines = self.projectFile.readlines()
            # remove comment lines
            self.projectFileData = [i for i in rawLines if i[0:2] != '##']
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
            self.ReadAnalysisComments()

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

            # good project file ?
            self.isValid = self.errors == []
        else:
            self.errors.append( '<%s> does not exist.' % self.projFileName)

    #-----------------------------------------------------------------------------------------------
    def ReadPaths( self):
        """ Write the project and src code root info to the file """
        self.paths[ePathProject] = self.GetLine( 'Path_ProjectRoot')
        self.paths[ePathSrcRoot] = self.GetList( 'Path_SrcCodeRoot')
        self.paths[ePathInclude] = self.GetList( 'Path_IncludeDirs')
        self.paths[ePathPcLint] = self.GetLine( 'Path_PcLint')
        self.paths[ePathU4c] = self.GetLine( 'Path_U4c')
        self.paths[ePathViewer] = self.GetLine( 'Path_Viewer')

        # verify all paths are valid
        for p in self.paths:
            v = self.paths[p]
            if type(v) == str:
                v = [v]

            for vx in v:
                if not vx or not self.CheckPath( vx):
                    self.errors.append( '%s Invalid Path/File: <%s>' % (p, vx))

        # normalize the paths
        # TODO: not needed when the proj builder is completed
        for vx,vl in enumerate(self.paths[ePathSrcRoot]):
            self.paths[ePathSrcRoot][vx] = os.path.normpath( vl)

        # TODO: not needed when the proj builder is completed
        for vx,vl in enumerate(self.paths[ePathInclude]):
            self.paths[ePathInclude][vx] = os.path.normpath( vl)


    #-----------------------------------------------------------------------------------------------
    def CheckPath( self, aPath):
        """ Validate the path info provided in the project file.
            This should ensure the actual case is provided when on Windows (although Windows does
            not care) because our relative path and fullPath check do care.
        """
        status = True
        # is it a directory
        if not os.path.isdir( aPath):
            # is it a file
            if not os.path.isfile(aPath):
                # how about the parts
                parts = aPath.split()
                current = parts[0]
                parts = parts[1:]
                while parts and not (os.path.isdir( current) or os.path.isfile( current)):
                    current = current + ' ' + parts[0]
                    parts = parts[1:]
                status = os.path.isdir( current) or os.path.isfile( current)

        return status

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
                # todo make sure the first line in the func/file_h/file_c descriptions does not
                # have a span :xx: in it, that is invalid
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
    def ReadAnalysisComments( self):
        self.analysisComments = self.GetList( eAnalysisComments)

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
    def WriteAnalysisComments( self):
        self.PutList( eAnalysisComments, self.analysisComments)

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
        """ Find the Project File header
        """
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
                # read until the next header
                if v and v[0] != '[' and v[-1] != ']':
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
                    # see if it is in the root dir
                    fpfn = os.path.join( i, title)
                    if os.path.isfile(fpfn):
                        fullPathNames.append( fpfn)
                    else:
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
        srcRoots = self.paths[ePathSrcRoot]

        # compute the relative path from a srcRoot
        fn = fpfn
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
