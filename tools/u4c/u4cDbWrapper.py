"""
Understand Db wrapper
This class wraps the Understand DB to make life easier for our analysis
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------

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
    def GetFuncInfo(self):
        """ This function returns the following data about all of the functions within a file
        """
        pass

    #-----------------------------------------------------------------------------------------------
    def GetFuncHeaders( self):
        """
        """
        funcs = self.db.ents('function')
        funcHeader = collections.OrderedDict()
        others = collections.OrderedDict()

        sf = funcs[:]
        sf.sort(key=lambda x:x.name())

        for func in sf:
            comment = g4.GetFuncHeader(func)
            if comment is not None:
                funcHeader[func.name()] = comment
                print( '-'*100)
                print( func.name())
                print( '-'*100)
                print( comment)
            else :
                others[func.name()] = comment

        print( '-'*100)
        for i in others:
            print( '%4s: %s' % (others[i], i))

        return funcHeader, others

    #-----------------------------------------------------------------------------------------------
    def GetFile( fn):
        """
        """
        files = db.ents('files')
        for i in files:
            if i.name().lower() == fn.lower(): # configurable based on host os
                return i
        return None

    #-----------------------------------------------------------------------------------------------
    def GetFileLexemes( fn):
        """
        """
        lexItems = []
        fo = GetFile( fn)
        if fo:
            fol = fo.lexer()
            lexItems = [i for i in fol]
        return lexItems

