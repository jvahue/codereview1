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
        try:
            # open the named DB
            self.db = understand.open( name)
            self.status = 'DB Open'
            self.isOpen = True
        except understand.DBAlreadyOpen:
            self.status = 'DB Already Open'
            self.isOpen = False
        except understand.DBCorrupt:
            self.status = 'DB Corrupt'
            self.isOpen = False
        except understand.DBOldVersion:
            self.status = 'DB Old Version'
            self.isOpen = False
        except understand.DBUnknownVersion:
            self.status = 'DB Unknown Version'
            self.isOpen = False
        except understand.DBUnableOpen:
            self.status = 'DB Unable to Open'
            self.isOpen = False
        except understand.NoApiLicense:
            self.status = 'DB API License Error'
            self.isOpen = False

        self.fileFuncInfo = {}

    #-----------------------------------------------------------------------------------------------
    def LookupItem(self, itemName, kindIs = None):
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
    def GetFileFunctionInfo(self, filename):
        """ return the function info for all function in a file
        """
        funcInfo = {}

        if filename not in self.fileFuncInfo:
            fileEnt = self.GetFileEnt( filename)

            if fileEnt is not None:
                functions = fileEnt.ents( 'Define', 'Function')

                lxr = fileEnt.lexer()
                returnsAt = self.GetReturnsInFile( lxr)

                for f in functions:
                    funcInfo[f.name()] = self.GetFuncInfo( f, returnsAt)
                    funcInfo[f.name()]['fullPath'] = self.GetFileEnt( filename).longname()

                self.fileFuncInfo[filename] = funcInfo
        else:
            funcInfo = self.fileFuncInfo[filename]

        return funcInfo

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
    def GetFuncInfo(self, function, returnsAt):
        """ This function returns the following data about all of the functions within a file
            Function Header
            Content
            StartLine, EndLine
            Metrics
        """
        info = OrderedDict()

        info['header'] = function.comments('before', True)
        info['content'] = function.contents()

        metrics = function.metric( function.metrics())

        # find the start, end line of the functions
        defRefs = function.refs()
        defRef = [i for i in defRefs if i.kindname() == 'Define']
        if len(defRef) == 1:
            info['start'] = defRef[0].line()
        else:
            lines = [i.line() for i in defRef]
            lines.sort()
            info['start'] = lines[0]
        info['end'] = info['start'] + (metrics['CountLine'] - 1)

        info['metrics'] = metrics

        info['returns'] = 0
        for l in returnsAt:
            if l >= info['start'] and l <= info['end']:
                info['returns'] += 1

        return info

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
            if info['start'] <= line <= info['end']:
                theFunc = func
                break

        return theFunc, info


#===================================================================================================
if __name__ == '__main__':
    dbName = r'D:\Knowlogic\Tools\CR-Projs\zzzCodereviewPROJ\tool\u4c\db.udb'
    db = U4cDb(dbName)
    a,b = db.InFunction( '', 47)
    itemRefs = db.LookupItem( 'va_list')
    for ref in itemRefs:
        print( ref.kindname(), ref.file(), ref.line(), ref.scope(), ref.ent().name())