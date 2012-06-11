"""
Understand Db wrapper
This class wraps the Understand DB to make life easier for our analysis
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
from collections import OrderedDict
import re

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

    #-----------------------------------------------------------------------------------------------
    def GetFileFunctionInfo(self, filename):
        """ return a list of functions in the file
        """
        functions = []
        fileEnt = self.db.lookup(re.compile(filename), 'File')

        if len(fileEnt) > 1:
            # find the exact match
            fileEnt = [i for i in fileEnt if i.name() == filename]

        functions = fileEnt[0].ents( 'Define', 'Function')

        lxr = fileEnt[0].lexer()
        returnsAt = self.GetReturnsInFile( lxr)

        funcInfo = {}
        for f in functions:
            funcInfo[f.name()] = self.GetFuncInfo( f, returnsAt)

        return funcInfo

    #-----------------------------------------------------------------------------------------------
    def GetReturnsInFile(self, lxr):
        """ return a list of line numbers where a return statement is performed
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

