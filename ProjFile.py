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

import inspect
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
            self.CreateProjectFile( ffn)
        else:
            self.Open()

    #-----------------------------------------------------------------------------------------------
    def Reset(self, ffn):
        """ Init/declare all the variable for this class
        """
        self.projFileName = ffn
        self.projName = os.path.splitext(os.path.split(ffn)[1])[0]

        self.paths = OrderedDict()
        self.paths['ProjectRoot'] = os.path.split(ffn)[0]
        self.paths['SrcCodeRoot'] = [] # a list of roots
        self.paths['IncludeDirs'] = [] # a list of include dirs
        self.paths['PcLint'] = ePcLintPath  # path to PcLint executable
        self.paths['U4c'] = eU4cPath        # path to U4c executable

        self.defines = []     # a list of defines
        self.undefines = []

        self.exclude = OrderedDict()
        self.exclude['Files_PcLint'] = []
        self.exclude['Files_U4c'] = []
        self.exclude['Functions'] = []
        self.exclude['Keywords'] = []

        self.formats = OrderedDict()
        self.formats['File_h'] = ''
        self.formats['File_c'] = ''
        self.formats['FunctionHeader'] = ''

        self.metrics = OrderedDict()
        self.metrics['complexityMcCabe'] = 10
        self.metrics['complexityNesting'] = 5
        self.metrics['lengthFile'] = 3000
        self.metrics['lengthFunction'] = 200
        self.metrics['lengthLine'] = 95
        self.metrics['functionReturns'] = 1

        self.naming = OrderedDict()
        self.naming['function'] = r'[A-Za-z0-9_]{1,32}'
        self.naming['variable'] = r'[A-Za-z0-9_]{1,32}'
        self.naming['enum'] = r'[A-Za-z0-9_]{1,32}'
        self.naming['constants'] = r'[A-Za-z0-9_]{1,32}'
        self.naming['defines'] = r'[A-Za-z0-9_]{1,32}'

        self.options = OrderedDict()
        self.options['PcLint'] = ''

        self.restricted = OrderedDict()
        self.restricted['Functions'] = []

        self.modified = False

    #-----------------------------------------------------------------------------------------------
    def CreateProjectFile(self, ffn):
        """ Create an default project file
        """
        self.modified = True
        self.Save()

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
            self.formats[i] = self.GetMultiLines( 'Format_%s' % i)

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
    def ReadNaming( self):
        at = self.GetHdr( 'Naming')
        if at != -1:
            at += 1
            while at < len(self.projectFileData):
                line = self.projectFileData[at]
                at += 1
                parts = line.strip().split('=')
                if len(parts) == 2:
                    self.naming[parts[0].strip()] = parts[-1]
                else:
                    break

    #-----------------------------------------------------------------------------------------------
    def ReadOptions( self):
        for i in self.options:
            self.options[i] = self.GetMultiLines( 'Options_%s' % i)

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
    def WriteOptions( self):
        self.PutDictItems( 'Options', self.options)

    #-----------------------------------------------------------------------------------------------
    def WriteRestricted( self):
        self.PutDictItems( 'Restricted', self.restricted)

    #-----------------------------------------------------------------------------------------------
    # Utilities
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


if __name__ == '__main__':
    pf = r'C:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ\G4.crp'
    pf1 = r'C:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ\G41.crp'
    pf2 = r'C:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ\G42.crp'
    pf0 = ProjectFile(pf)
    pf0.modified = True
    pf0.Save(pf1)