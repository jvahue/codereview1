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

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
import ViolationDb

from tools.pcLint import PcLintFileTemplates
from tools.pcLint.KsCrLnt import LintLoader
from tools.ToolMgr import ToolSetup, ToolManager

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eDefaultToolPath = r'C:\lint\lint-nt.exe'
eToolRoot = r'tool\pclint'

eBatchName = r'runLint.bat'
eSrcFilesName = r'srcFiles.lnt'
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
            toolExe = eDefaultToolPath

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
    def __init__(self, projRoot, toolExe = None):
        ToolManager.__init__(self, projRoot)

        if toolExe is None:
            self.toolExe = eDefaultToolPath
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
    def CleanLint( self):
        """ Load the new Lint info into the DB
            new items
            repeat open items
            repeats closed items
        """
        eFieldCount = 6
        # open the source file
        finName = os.path.join( self.projToolRoot, eResultFile)
        print( '\nCleanup %s\n' % finName)
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

        # open the PCLint DB
        sl3 = ViolationDb.ViolationDb( self.projRoot)
        sl3.DebugState( 1)

        # move to the DB
        lintLoader = LintLoader( finName, sl3)
        lintLoader.RemoveDuplicate()
        removed, updateTime = lintLoader.InsertDb( lintLoader.reducedData)

        # print stats
        print( 'Inserted %5d New' % sl3.insertNew)
        print( 'Updated  %5d Records' % sl3.insertUpdate)
        print( 'Select Errors: %d' % sl3.insertSelErr)
        print( 'Insert Errors: %d' % sl3.insertInErr)
        print( 'Update Errors: %d' % sl3.insertUpErr)

        # remove the old PcLint violations
        s = "delete from violations where lastReport != ? and detectedBy = 'PcLint'"
        sl3.Execute( s, (updateTime,))
        sl3.Commit()
        print( 'Removed %d Old Records - %s' % (removed, updateTime))

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
    -iC:\Knowlogic\clients\PWC\proj\FAST\dev\appl\G4E\G4_CP\test
    """

options = {}
options['sizeOptions'] = """
-si4 -sp4

"""

misc = """
+macros  // make macros accept string 2*4096
+fem // needed for things like __interrupt void TTMR_GPT0ISR
-D__m68k

+libdir(D:\Knowlogic\clients\PWC\FAST_Testing\dev\G4E\GhsInclude)
-wlib(1) // turn off lib warnings

-e793
-e830
-e831

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

    tool.CleanLint()
    tool.LoadDb()

def Clean():
    tool = PcLint( projRoot)
    tool.Review()
    tool.CleanLint()


    print('\nall done\n')

def Load():
    tool = PcLint( projRoot)
    tool.LoadDb()

if __name__ == '__main__':
    #TestCreate()
    TestRun()
    #Clean()
    #Load()