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

eBatchName = r'runLint.bat'
eLntSrcFileName = r'srcFiles.lnt'
eResultFile = r'results\result.csv'

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
        self.CreateFile( eBatchName, batTmpl % (toolExe, pcLintRoot, eResultFile))
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

    #-----------------------------------------------------------------------------------------------
    def CleanUp( self):
        """  Celan up the PcLint output - remove file names, blank lines
          Insert into the DB and count
            new items
            repeat open items
            repeats closed items
        """
        fn0 = os.path.join( self.projToolRoot, eResultFile)
        print( '\nCleanup %s\n' % fn0)
        fi = open( fn0, 'r', newline='')
        csvIn = csv.reader( fi)

        fno = os.path.splitext( fn0)[0] + '_1.csv'
        fo = open( fno, 'w',newline='')
        csvOut = csv.writer(fo)

        csvOut.writerow(['Cnt','Filename','Function','Line','Type','ErrNo','Description'])

        lineNum = 0
        for l in csvIn:
            lineNum += 1
            if len( l) > 0:
                if l[0].find('---') == -1:
                    if len(l) != 6:# and l[1:6] == l[6:]:
                        l = l[:6]

                    # remove full pathname
                    if l[0] and l[0][0] != '.':
                        path, fn = os.path.split(l[0])
                        subdir = os.path.split( path)[1]
                        l = [r'%s\%s' % (subdir, fn)] + l[1:]

                    opv = [1] + l
                    csvOut.writerow(opv)
                else:
                    print('Delete[%4d]: %s' % (lineNum, ','.join(l)))
            else:
                print('Delete[%4d]: Blank Line' % ( lineNum))

        fo.close()
        fi.close()

        # rename
        #os.remove( fn0)
        #os.rename( fno, fn0)


#========================================================================================================================
import socket
host = socket.gethostname()

if host == 'Jeff-Laptop':
    projRoot = r'D:\Knowlogic\zzzCodereviewPROJ'
    srcCodeRoot = r'D:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP'
    incStr = r"""
    -iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\GhsInclude
    -iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\application
    -iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\drivers
    -iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\drivers\hwdef
    -iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\system
    -iD:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\G4_CP\test
    """
else:
    projRoot = r'C:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ'
    srcCodeRoot = r'C:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\G4_CP'
    incStr = r"""
    -iC:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\GhsInclude
    -iC:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\G4_CP\application
    -iC:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\G4_CP\drivers
    -iC:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\G4_CP\drivers\hwdef
    -iC:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\G4_CP\system
    -iC:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\G4_CP\tes
    """

options = {}
options['sizeOptions'] = """
-si4 -sp4

"""

misc = """
+fem // needed for things like __interrupt void TTMR_GPT0ISR
-D__m68k

+libdir(D:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\GhsInclude)
+macros  // make macros accept string 2*4096
-wlib(1) // turn of lib warnings

"""

def TestCreate():
    includes = [i.strip() for i in incStr.split('\n') if i.strip() ]
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

def TestRun():
    ps = PcLintSetup( projRoot)
    ps.FileCount()
    tool = PcLint( projRoot)
    tool.Review()
    lastSize = 119
    counter = 1
    while tool.ReviewActive():
        newSize = os.path.getsize( tool.stdout.name)
        if (newSize - lastSize) > len('--- Module:   '):
            lastSize = newSize
            print( '%d of %d: %d' % (counter, ps.fileCount, newSize))
            counter += 1

    tool.CleanUp()

def Clean():
    tool = PcLint( projRoot)
    tool.Review()
    tool.CleanUp()


    print('\nall done\n')

TestCreate()
TestRun()
#Clean()