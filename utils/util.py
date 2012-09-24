#==============================================================================================
#
# Description: Utility Functions
#
#==============================================================================================
import datetime
import os
import time
import _thread
from types import *

from . import pprintjv
from . import DateTime
import collections

#----------------------------------------------------------------------------------------------
# Module Data
days = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
secPerHour = 3600
secPerDay = secPerHour * 24
zeroDate = '1/1/1970'
zeroSeconds = 18000.0
timeFormat = "%a %b %d %H:%M:%S %Y"
MMDDYYYY = "%m/%d/%Y"
ISO_FMT = "%Y-%m-%d %H:%M:%S"


#----------------------------------------------------------------------------------------------
def IntSelect( aStr, theMin, theMax):
    """ Display a list of choices and limit the user input the the input options
        Return and INT
    """
    select = theMin - 1
    while select == (theMin - 1):
        try:
            select = int( input( aStr))
            if select < theMin or select > theMax:
                print('\nSorry', select, 'is not an option.')
                print('Enter a number between', theMin, 'and', theMax, '.')
                select = theMin - 1
        except ValueError:
            print('You have to enter a number.')
            select = theMin -1

    return select

#----------------------------------------------------------------------------------------------
def SelectStr( aList):
    """ Let the user select a string from a list of strings
        Return the choice element from the list
    """
    # ensure we have a list
    copyList = list(aList)
    theMin = 1
    theMax = len(aList)
    aStr = "\n"
    for i in copyList:
        aStr += "  %2d. %s\n" % (copyList.index(i)+1, i)
    pos = IntSelect( aStr, theMin, theMax) - 1
    return copyList[pos]

#----------------------------------------------------------------------------------------------
def SelectInt( aList):
    # ensure we have a list
    copyList = list(aList)
    theMin = 1
    theMax = len(aList)
    aStr = '\n'
    for i in copyList:
        aStr += "  %2d. %s\n" % (copyList.index(i)+1, i)
    aStr += "Make a selection: "
    return IntSelect( aStr, theMin, theMax) - 1

#----------------------------------------------------------------------------------------------
#----- TIME CONVERSIONS
#----------------------------------------------------------------------------------------------
def StringToSeconds( aStr, fmt = timeFormat):
    """ assumes Date aStr format is 'Thu 28 Jun 2001 14:17:15' """
    seconds = zeroSeconds
    # check for a date that could not be converted
    # (i.e., only 1970 < date < 2038)
    try:
        seconds = time.mktime( time.strptime( aStr, fmt))
    except:
        print("*** ERROR: Date: ", aStr)

    return seconds

#----------------------------------------------------------------------------------------------
def SecondsToString( seconds, format = timeFormat):
    """ assumes Date str format is 'Thu 28 Jun 2001 14:17:15' """
    try:
        string = strftime( format, seconds)
    except:
        string = ''

    return string

#----------------------------------------------------------------------------------------------
def TimeToSeconds( theTime = None):
    """Return time as seconds"""
    seconds = zeroSeconds
    try:
        theType = type(theTime)

        if theType == NoneType:
            # get the current time
            seconds = time.mktime( time.localtime())
        elif theType in (FloatType, IntType, LongType):
            if seconds >= zeroSeconds:
                seconds = theTime
        elif theType == StringType:
            # guess at the string format 06/12/1999
            if len( theTime) > 10:
                seconds = StringToSeconds( theTime)
            else:
                seconds = StringToSeconds( theTime, MMDDYYYY)
        elif theType == TupleType or theType == time.struct_time:
            seconds = time.mktime( theTime)
        else:
            timeStr = str( theTime)
            seconds = StringToSeconds( timeStr)
    except (OverflowError, ValueError, TypeError):
        seconds = zeroSeconds

    return seconds

#------------------------------------------------------------------------------
def TimeToString( theTime, fmt = timeFormat):
    """Return Date formatted as mm/dd/yyyy"""
    seconds = TimeToSeconds( theTime)
    d = time.localtime( seconds)
    return time.strftime( fmt, d)

#------------------------------------------------------------------------------
def MakeMMDDYYYY( theTime):
    """Return Date formatted as mm/dd/yyyy"""
    return TimeToString( theTime, MMDDYYYY)

#------------------------------------------------------------------------------
def TimeDelta( t1, t2):
    """Compute t1 - t2 returns seconds"""
    s1 = TimeToSeconds( t1)
    s2 = TimeToSeconds( t2)

    return s1 - s2

#------------------------------------------------------------------------------
def ValidFileName( name):
    """Change invalid file characters into underscores and return the new file name"""
    fileName = name
    for i in '\\/:*?"<>|':
        fileName = fileName.replace( i, '_')
    return fileName

#------------------------------------------------------------------------------
def ConvertDBtime( date):
    # convert DbiDate to DateTime
    return DateTime.DateTime.fromtimestamp(TimeToSeconds(date))

#----------------------------------------------------------------------------------------------
def GetDate( msg):
    dateStr = ''
    while dateStr == '':
        dateStr = input( "Enter a %s date [mm/dd/yyyy]: " % (msg))
        try:
            date = time.strptime( dateStr, "%m/%d/%Y")
        except:
            print("Use the format mm/dd/yyyy")
            dateStr = ''

    return date

#----------------------------------------------------------------------------------------------
def GetDateTime(m):
    """ Return a datetime object from user input """
    return datetime.datetime.fromtimestamp( TimeToSeconds( GetDate(m)))

#----------------------------------------------------------------------------------------------
def Str2Date( date):
    """ Return a datetime object from a string input """
    if date and type(date) == str:
        dt = DateTime.DateTime.utcnow()
        date = dt.Set(date).date()
    return date

#------------------------------------------------------------------------------------------
def GetExpiration( month, year):
    """ Compute Expiration Date for a month and year input """
    exp = datetime.date(year, month, 1)

    # get day of week for 1st day of month
    weekday = exp.weekday()
    daysToClosestFriday = 4 - weekday  # 4 is Friday
    if daysToClosestFriday < 0:
        bias = 21
    else:
        bias = 14
    bias += daysToClosestFriday
    expirationDate = exp + datetime.timedelta( bias)

    return expirationDate

#----------------------------------------------------------------------------------------------
def OpenCreatePath( filename, mode):
    """ Open a file creating a path to it if it does not exist """
    if not os.path.isfile( filename):
        path = os.path.split( filename)[0]
        if not os.path.isdir( path):
            os.makedirs(path)

    return open( filename, mode)

#----------------------------------------------------------------------------------------------
def igetattr( obj, thing, default, acceptNone=True):
    """ Return a targeted item in an object ensuring that something is returned. This
        function walks down into an object based on thing that is thing is formattered
        as a multiple object select "a.b.c.d".  This function walks down into c to get d.

        Use this instead of getattr if the object you want to get an attribute from is
        a component of another object and you know you top-level object exists, but don't know
        about the existence of any of its components.
    """
    class ERROR:
        """ Error Marker-different than None because something's value could be None """
        pass

    if type(thing) == str:
        errorMarker = ERROR()
        items = thing.split('.')
        obj = getattr( obj, items[0], errorMarker)
        items = items[1:]
        while obj is not errorMarker and items:
            obj = getattr( obj, items[0], errorMarker)
            items = items[1:]
        if obj is not errorMarker:
            if acceptNone:
                return obj
            elif obj is not None:
                return obj
            else:
                return default
        else:
            return default
    else:
        raise TypeError

#----------------------------------------------------------------------------------------------
class Output:
    """ This object provides for easy outputting of data to a delimited file.  The user can
        add fields via the AddItem or AddItems methods and this object will ensure the data is
        output in the sequenece provided and in the correct format.  Additionally the object
        can reset output values as requested by the caller after each call to write.
    """
    #------------------------------------------------------------------------------------------
    def __init__( self, delimiter, f = None, unset='-'):
        """ __init__( self, delimiter, f = None, unset='-')
            Init the output object, specify the delimter, file to write to, and an unset
            value str
        """
        self.f = f
        self.delimeter = delimiter
        self.unset = unset

        self.Reset()

    #------------------------------------------------------------------------------------------
    def Reset( self):
        """ reset the output object """
        self.writeHeader = True
        self.sequence = []
        self.fmt = []
        self.reset = []
        self.length = 0

    #------------------------------------------------------------------------------------------
    def AddItems( self, aList):
        """ Add a list of items for output.
            The list consists of 3-tuples of (Name, Format, Reset)
            Only allow addition prior to the first write.
        """
        if self.writeHeader:
            for name, fmt, reset in aList:
                self.AddItem( name, fmt, reset)
        else:
            raise NotImplementedError

    #------------------------------------------------------------------------------------------
    def AddItem( self, name, fmt, reset):
        """ Add an item to the output object, sequence, format and reset status are saved
            Only allow addition prior to the first write.
        """
        if self.writeHeader:
            self.sequence.append( name)
            self.fmt.append( fmt)
            self.reset.append( reset)
            self.length = len(self.sequence)

            # initialize the value
            setattr( self, name, None)
        else:
            raise NotImplementedError

    #------------------------------------------------------------------------------------------
    def ChangeFile( self, f):
        self.f = f
        self.writeHeader = True

    #------------------------------------------------------------------------------------------
    def write( self):
        """ Write the object to a delimited file """
        if self.f:
            if self.writeHeader:
                self.WriteHeader()
                self.writeHeader = False

            for i in range( self.length):
                name = self.sequence[i]
                fmt = self.fmt[i]
                value = getattr(self, name, None)

                # reset the value if user requested that
                if self.reset[i]:
                    setattr( self, name, None)

                if value is None:
                    self.f.write(self.unset)
                else:
                    try:
                        self.f.write( fmt % value)
                    except TypeError:
                        self.f.write( 'TypeError: %s for %s' % (fmt, str(value)))

                # add the delimeter (column)
                if i < (self.length-1):
                    self.f.write( self.delimeter)

            # and end the line (row)
            self.f.write('\n')
        else:
            raise RuntimeWarning("No file defined for Class Output!")

    #------------------------------------------------------------------------------------------
    def WriteHeader( self):
        """ Write the header as it exists """
        header = self.delimeter.join( self.sequence)
        self.f.write( header + '\n')


#----------------------------------------------------------------------------------------------
class ThreadSignal:
    """ Wrap a job and signal when it is done
    """
    def __init__( self, job=None, aClass = None):
        self.classRef = aClass
        if job:
            self.job = job
        else:
            self.job = self.NoJob
        self.active = False

    def Go( self):
        self.active = True
        _thread.start_new_thread( self.RunJob, ())

    def RunJob( self):
        try:
            self.job()
        except:
            import sys
            import traceback
            #xcptData = sys.exc_info()
            #t,v,tb = xcptData
            f = open('xcpt_%d.dat' % id(self), 'w')
            cName = '' if self.classRef is None else self.classRef.__class__.__name__
            fName = self.job.__name__
            f.write( 'Class: %s Func: %s\n' % ( cName, fName))
            f.write( 'UTC: %s Local: %s\n' % ( datetime.datetime.utcnow(), datetime.datetime.now()))
            traceback.print_exc( 20, f)
            f.close()
            #print_exception( t,v,tb,file = f)
        self.active = False

    def NoJob( self):
        pass

#==============================================================================================
class ShowObject:
    """ Objects that can show themselves """
    #------------------------------------------------------------------------------------------
    def Show( self):
        subItems = []
        iterables = []
        print('-' * 50)
        #print 'Show %s' % str(self)
        d = dir(self)
        d.sort()
        for i in d:
            item = getattr(self,i)
            # if not callable and not an object method
            if not isinstance( item, collections.Callable) and i[:2] != '__':
                subItem = getattr( item, 'Show', None)
                if subItem:
                    subItems.append( subItem)
                elif type(item) in (list, tuple, dict):
                    iterables.append( (i, item))
                elif type(item) == float:
                    print('%-30s: %.2f' % (i,item))
                else:
                    print('%-30s:' % (i), item)
        # show the iterables
        for i,d in iterables:
            ti = type(d)
            print('>' * 5, i, ti, '<' * 20)
            if ti == dict:
                for k in d:
                    print(k, d[k])
            else:
                oneLine = (type(d[0]) == str or len(d[0]) == 1)
                pprintjv.Show(d, oneLine)
        # show the subitems
        for i in subItems:
            i()

#----------------------------------------------------------------------------------------------
class Holder( ShowObject):
    """ Empty class to hold whatever is needed """
    def __init__( self, **kw):
        for i in kw:
            setattr( self, i, kw[i])

    #------------------------------------------------------------------------------------------
    def __repr__( self):
        m = []
        d = dir(self)
        d.sort()
        for i in d:
            item = getattr(self,i)
            # if not callable and not an object method
            if not isinstance( item, collections.Callable) and i[:2] != '__':
                m.append( '%s=%s' % (i, str(item)))

        return '\n'.join(m)

    #------------------------------------------------------------------------------------------
    def __eq__( self, other):
        """ Compare the contents of both objects """
        status = True
        # 1. Verify all fields are the same
        if other and list(self.__dict__.keys()) == list(other.__dict__.keys()):
            # 2. check all the values for each item
            for i in list(self.__dict__.keys()):
                sv = getattr( self, i)
                ov = getattr( other, i)
                if sv != ov:
                    status = False
                    break
        else:
            status = False
        return status

    #------------------------------------------------------------------------------------------
    def Dup( self, other):
        """ Copy one holder's data to another """
        for i in dir( other):
            item = getattr( other, i)
            # if not callable and not an object attribute
            if not isinstance( item, collections.Callable) and i[:2] != '__':
                setattr(self, i, item)

#----------------------------------------------------------------------------------------------
def dtx( s, dt):
    """ Convert a string date time rep into whatever dt is (i.e., date or datetime) """
    ds = DateTime.DateTime.utcnow()
    ds = ds.Set(s)
    if type( dt) == datetime.date:
        return datetime.date( ds.year, ds.month, ds.day)
    elif type( dt) == datetime.datetime:
        return datetime.datetime( ds.year, ds.month, ds.day,
                                  ds.hour, ds. minute, ds.second, ds.microsecond)
    else:
        raise TypeError('dt parameter needs to be either date or datetime')
    return

#--------------------------------------------------------------
def TestChoice():
    aStr = \
"""
1. Hello
2. good
3. bad"""
    print(IntSelect(aStr, 1,3))
    aList = ['first', 'second', 'third']
    aTup = tuple(aList)
    print(SelectStr( aList))
    print(SelectStr( aTup))
    print(SelectInt( aList))
    print(SelectInt( aTup))

if __name__ == '__main__':
    h0 = Holder(a=1,b=2,c=[1,3])
    h1 = Holder(a=1,b=2,c=[1,2])
    e1 = h0 == h1


"""
///////////////////////////////////////////////////////////////////////////////////////////////
$History: util.py $
 *
 * *****************  Version 18  *****************
 * User: Vahue        Date: 3/29/06    Time: 6:16p
 * Updated in $/Scripts/Common
 * Add reset capabilities to the Output object
 *
 * *****************  Version 17  *****************
 * User: Vahue        Date: 3/28/06    Time: 10:23a
 * Updated in $/Scripts/Common
 * Fix output display
 *
 * *****************  Version 16  *****************
 * User: Vahue        Date: 1/04/06    Time: 11:50a
 * Updated in $/Scripts/Common
 * mod ConvertDBtime to use DateTime
 *
 * *****************  Version 15  *****************
 * User: Vahue        Date: 12/07/05   Time: 7:13p
 * Updated in $/Scripts/Common
 * Allow changing output file
 *
 * *****************  Version 14  *****************
 * User: Vahue        Date: 11/23/05   Time: 11:29a
 * Updated in $/Scripts/Common
 * Add ability to output header from output object on request
 *
 * *****************  Version 13  *****************
 * User: Vahue        Date: 11/23/05   Time: 9:40a
 * Updated in $/Scripts/Common
 * Provide Standard Output Object
///////////////////////////////////////////////////////////////////////////////////////////////
"""

