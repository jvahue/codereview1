"""
This file implements a result row object.  These objects allow you to access the fields of a query
by the field name used in a query.
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

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
class ResultRow:
    def __init__( self, fields, data):
        self.data = data
        self.fields = fields
        try:
            self.length = len( data)
        except TypeError:
            self.length = 0
        self.index = 0

    #------------------------------------------------------------------------------------------
    def __str__( self):
        return str( self.data)

    #------------------------------------------------------------------------------------------
    def __repr__( self):
        return str( self.data)

    #------------------------------------------------------------------------------------------
    def __eq__( self, other):
        if isinstance( other, ResultRow):
            return self.data == other.data
        else:
            return self.data == other

    #------------------------------------------------------------------------------------------
    def __len__( self):
        return self.length

    #------------------------------------------------------------------------------------------
    def __getitem__( self, key):
        if type(key) == slice:
            return self.data[key.start:key.stop:key.step]
        elif abs(key) <= self.length:
            return self.data[key]
        else:
            raise IndexError

    #------------------------------------------------------------------------------------------
    def __getattr__( self, name):
        """ when only one field is requested from the query self.fields = [] so we just return
            the atomic value fetched
        """
        if self.data:
            if name in self.fields:
                x = self.fields.index(name)
                return self.data[x]
            elif self.fields == []:
                return self.data
            else:
                raise AttributeError
        else:
            return None

    #------------------------------------------------------------------------------------------
    def __iter__(self):
        """ Initialize the iterator """
        self.index = 0
        return self

    #------------------------------------------------------------------------------------------
    def __next__( self):
        """ Get the next row form the data set """
        if self.index < self.length:
            rv = self.data[ self.index]
            self.index += 1
            return rv
        else:
            raise StopIteration

