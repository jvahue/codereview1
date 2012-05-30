"""
PC-Lint Tool Manager

Design Assumptions:
1. A .lnt file with all source code files to be analyzed is created during tool setup
2. The .lnt file is located in the PcLint subdir of CodeReview
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import os
import sys
import time

sys.path.append( '..')

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
import PcLintFileTemplates

from ToolMgr import ToolSetup, ToolManager

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eDefaultPcLintPath = r'C:\lint\lint-nt.exe'
eToolRoot = r'tool\pclint'

eBatchName = 'runLint.bat'
eLntSrcFileName = 'srcFiles.lnt'

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
class PcLintSetup( ToolSetup):
    def __init__( self, projRoot):
        """ Handle all PcLint setup
        """
        ToolSetup.__init__( self, projRoot)
        self.projToolRoot = os.path.join( self.projRoot, eToolRoot)
        self.fileCount = 0

    #-----------------------------------------------------------------------------------------------
    def CreateProject( self, srcCodeFiles, options, toolExe=None):
        """ Create all of the files needed for this project
            1. runLint.bat - the main file to run PC-Lint
            2. srcFile.lnt - a listing of all the src files
            3. A format file for the lint output to csv files
        """

        batTmpl = PcLintFileTemplates.ePcLintBatTemplate
        optTmpl = PcLintFileTemplates.eOptionsTemplate

        if toolExe is None:
            toolExe = eDefaultPcLintPath

        # get the PcLint Root
        pcLintRoot = os.path.split( toolExe)[0]

        # create the required files
        self.CreateFile( eBatchName, batTmpl % (toolExe, pcLintRoot))
        self.CreateFile( 'options.lnt', optTmpl.format_map(options))
        self.CreateFile( 'srcFiles.lnt', '\n'.join(srcCodeFiles))

        self.fileCount = len( srcCodeFiles)

    #-----------------------------------------------------------------------------------------------
    def CreateFile( self, name, content):
        """  creates the named file with the specified contents
        """
        pcLintPath = os.path.join( self.projRoot, eToolRoot, name)
        ToolSetup.CreateFile( self, pcLintPath, content)

    #-----------------------------------------------------------------------------------------------
    def FileCount( self):
        f = open( os.path.join( self.projToolRoot, 'srcFiles.lnt'), 'r')
        lines = f.readlines()
        f.close()
        self.fileCount = len( lines)

#---------------------------------------------------------------------------------------------------
class PcLint( ToolManager):
    def __init__(self, projRoot, toolExe = None):
        ToolManager.__init__(self, projRoot)

        if toolExe is None:
            self.toolExe = eDefaultPcLintPath
        else:
            self.toolExe = toolExe

        self.projToolRoot = os.path.join( self.projRoot, eToolRoot)

    #-----------------------------------------------------------------------------------------------
    def Review(self):
        """ Run a Review based on this tools capability.  This is generally a two step process:
          1. Update the tool output
          2. Generate Reivew data
        """
        # Run the PC-Lint bat file
        self.jobCmd = '%s' % os.path.join( self.projToolRoot, eBatchName)
        ToolManager.Review(self)


#========================================================================================================================
projRoot = r'D:\Knowlogic\zzzCodereviewPROJ'
srcCodeRoot = r'D:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP'
options = {}
options['sizeOptions'] = '-si4 -sp4'

incStr = r"""
-iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\GhsInclude
-iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\application
-iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\drivers
-iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\drivers\hwdef
-iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\system
-iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\test

+libdir(D:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\GhsInclude)
+macros  // make macros accept string 2*4096
-wlib(1) // turn of lib warnings

"""

def TestCreate():
    includes = [i.strip() for i in incStr.split('\n') if i.strip() ]
    options['includes'] = '\n'.join(includes)

    options['defines'] = '-D__m68k'

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

def TestRun():
    ps = PcLintSetup( projRoot)
    ps.FileCount()
    tool = PcLint( projRoot)
    tool.Review()
    lastSize = 119
    counter = 1
    while 1 and tool.ReviewActive():
        newSize = os.path.getsize( tool.stdout.name)
        if (newSize - lastSize) > len('--- Module:   '):
            lastSize = newSize
            print( '%d of %d: %d' % (counter, ps.fileCount, newSize))
            counter += 1


    print('\nall done\n')

#TestCreate()
TestRun()