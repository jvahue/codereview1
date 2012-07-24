"""
Understand Db wrapper
This class wraps the Understand DB to make life easier for our analysis
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
from collections import OrderedDict

import re
import os

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------
import understand

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eFiHeader = 'header'
eFiFullPath = 'fullPath'
eFiContent = 'content'
eFiStart = 'start'
eFiEnd = 'end'
eFiMetrics = 'metrics'
eFiReturns = 'returns'
eFiParams = 'parameters'
eFiParamsTypes = 'paramTypes'
eDeclareDefine = 'decDef'
eFiReturnType = 'returnType'

eFiMxLines = 'CountLine'

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
class U4cDb:
    """
    Class description
    """
    #-----------------------------------------------------------------------------------------------
    def __init__(self, name):
        # two tries to open the DB
        self.db = None
        tryCount = 0
        while self.db is None and tryCount < 3:
            tryCount += 1
            try:
                # open the named DB
                self.db = understand.open( name)
                self.status = 'DB Open'
                self.isOpen = True
            except understand.UnderstandError as e:
                self.db = None
                self.status = str(e)
                self.isOpen = False

        # hold function info for all requested functions
        self.fileFuncInfo = {}

    #-----------------------------------------------------------------------------------------------
    def __del__(self):
        """ delete the db connection """
        if self.db:
            del self.db

    #-----------------------------------------------------------------------------------------------
    def FindEnt(self, item):
        """ Find where an entity is defined or declared """
        # check for declared first
        defFile, defLine = self.RefAt( item, 'Declare')
        if defFile == '':
            defFile, defLine = self.RefAt( item)
        return defFile, defLine

    #-----------------------------------------------------------------------------------------------
    def GetFileEnt(self, filename):
        """ return the full path file name
        """
        title = os.path.split(filename)[1]

        fileEnt = self.db.lookup(re.compile(title, re.I), 'File')

        if len(fileEnt) > 1:
            # find the exact match
            fileEnt = [i for i in fileEnt if i.name() == title]

        return fileEnt[0] if fileEnt else None

    #-----------------------------------------------------------------------------------------------
    def GetFileFunctionInfo(self, filename):
        """ return the function info for all function in a file
        """
        funcInfo = {}

        if filename not in self.fileFuncInfo:
            fileEnt = self.GetFileEnt( filename)

            if fileEnt is not None:
                functions = fileEnt.ents( 'Define', 'Function')

                # incase someone deleted the file let's check
                if os.path.isfile( fileEnt.longname()):
                    lxr = fileEnt.lexer()
                    returnsAt = self.GetReturnsInFile( lxr)

                    for f in functions:
                        funcInfo[f.name()] = self.GetFuncInfo( f, returnsAt)
                        funcInfo[f.name()][eFiFullPath] = self.GetFileEnt( filename).longname()

                    self.fileFuncInfo[filename] = funcInfo
        else:
            funcInfo = self.fileFuncInfo[filename]

        return funcInfo

    #-----------------------------------------------------------------------------------------------
    def GetFuncInfo(self, function, returnsAt):
        """ This function returns the following data about all of the functions within a file
            Function Header
            Content
            StartLine, EndLine
            Metrics
        """
        info = OrderedDict()

        info[eFiHeader] = function.comments('before')
        info[eFiContent] = function.contents()

        metrics = function.metric( function.metrics())

        # find the start, end line of the functions
        defFile, defLine = self.RefAt( function)
        info[eFiStart] = defLine
        info[eFiEnd] = info[eFiStart] + (metrics[eFiMxLines] - 1)

        info[eFiMetrics] = metrics

        # get params names: and return type
        theRefs = function.refs()
        info[eFiParams] = []
        info[eFiParamsTypes] = []
        for r in theRefs:
            if r.ent().kindname() == 'Parameter' and r.kindname() == 'Define':
                info[eFiParams].append( r.ent().name())
                info[eFiParamsTypes].append( r.ent().type())

        info[eFiReturnType] = function.type()

        # declare/define
        decFile, decLine = self.RefAt( function, 'Declare')
        defFile, defLine = self.RefAt( function, 'Define')
        info[eDeclareDefine] = ((decFile, decLine), (defFile, defLine))

        # count how many returns there are in the functions
        info[eFiReturns] = 0
        for l in returnsAt:
            if l >= info[eFiStart] and l <= info[eFiEnd]:
                info[eFiReturns] += 1

        return info

    #-----------------------------------------------------------------------------------------------
    def GetItemRefs(self, itemName, kindIs = None):
        """ Search the udb for an object named itemname
            return all references to it
        """
        if kindIs:
            item = self.db.lookup( re.compile(itemName), kindIs)
        else:
            item = self.db.lookup( re.compile(itemName))

        if len(item) > 1:
            item = [i for i in item if i.longname() == itemName]

        itemRefs = []
        if item and item[0].longname() == itemName:
            itemRefs = item[0].refs()

        return itemRefs

    #-----------------------------------------------------------------------------------------------
    def GetReturnsInFile(self, lxr):
        """ return a list of line numbers where a return statement is performed in a function
        - the lxr is the function of interest
        """
        returnsAt = []
        for l in lxr:
            if l.text() == 'return':
                returnsAt.append( l.line_begin())

        return returnsAt

    #-----------------------------------------------------------------------------------------------
    def InFunction(self, filename, line):
        """ This funtion returns the function that contains a line number in a filename
        """
        if filename not in self.fileFuncInfo:
            funcInfo = self.GetFileFunctionInfo( filename)
            if funcInfo:
                self.fileFuncInfo[filename] = funcInfo
        else:
            funcInfo = self.fileFuncInfo[filename]

        theFunc = 'N/A'
        info = {}
        for func in funcInfo:
            info = funcInfo[func]
            if info[eFiStart] <= line <= info[eFiEnd]:
                theFunc = func
                break

        return theFunc, info

    #-----------------------------------------------------------------------------------------------
    def RefAt(self, item, refType = 'Define'):
        """ find out where an item (ent) is declared
            returns:
              file: file where declared
              line: the line number of the declaration
        """
        defRefs = item.refs()
        defRef = [i for i in defRefs if i.kindname() == refType]

        if defRef == []:
            defFile = ''
            defLine = -1
        elif len(defRef) == 1:
            defFile = defRef[0].file()
            defLine = defRef[0].line()
        else:
            # find the first line in the define
            defLine = 1e6
            for i in defRef:
                if i.line() < defLine:
                    defFile = i.file()
                    defLine = i.line()

        return defFile, defLine

#===================================================================================================
if __name__ == '__main__':
    dbName = r'C:\Knowlogic\Tools\CR-Projs\zzzCodereviewPROJ\tool\u4c\db.udb'
    db = U4cDb(dbName)
    f = db.GetFileEnt('alt_Time.h')
    lxr = f.lexer()
    for i in db.GetLexerLine( lxr):
        print(i)
