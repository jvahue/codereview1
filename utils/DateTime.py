#==============================================================================================
#
# DateTime.py
#
# Descritpion: This file extends the datetime classes to improve display and add a few
# functions, that seem to come in handy.
#
#==============================================================================================
#----------------------------------------------------------------------------------------------
# Py Modules
from . import datetime
import re

#----------------------------------------------------------------------------------------------
# Altair Modules

#----------------------------------------------------------------------------------------------
delimiters = r'-/\.'

#  01234567890
# '2006-01-03 14:00:57.127000'
# Date formats

ISOdate = r'[0-9]{4}[%s][0-9]{1,2}[%s][0-9]{1,2}' % (delimiters,delimiters)
YMDdate = r'[0-9]{2,4}[%s][0-9]{1,2}[%s][0-9]{1,2}' % (delimiters,delimiters)
MDYdate = r'[0-9]{1,2}[%s][0-9]{1,2}[%s][0-9]{2,4}' % (delimiters,delimiters)

dateStrings = { ISOdate:'YMDdateParse', YMDdate:'YMDdateParse', MDYdate:'MDYdateParse'}

# time formats
ISOtime = r'[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}[.0-9]{0,7}'
HMtime  = r'[0-9]{1,2}:[0-9]{1,2}'

timeStrings = { ISOtime:'ISOtimeParse', HMtime:'HRtimeParse'}

#----------------------------------------------------------------------------------------------
class DateTime( datetime.datetime):
    #------------------------------------------------------------------------------------------
    def Set( self, timeStr):
        """ Set a time based on a string """
        # determine the format of the string
        for dre in dateStrings:
            da,ti = self.CheckFormat( dre, timeStr)
            if da:
                date = getattr(self, dateStrings[dre])(da)
                for tre in timeStrings:
                    ts,dummy = self.CheckFormat( tre, ti)
                    if ts:
                        time = getattr(self,timeStrings[tre])(ts)
                        dt = DateTime( date.year, date.month, date.day,
                                       time.hour, time.minute, time.second, time.microsecond)
                        return dt
                else:
                    dt = DateTime(date.year,date.month,date.day,0,0,0,0)
                    return dt
        else:
            raise ValueError('Invalid TimeStr: <%s>' % timeStr)

    #------------------------------------------------------------------------------------------
    def SetTime( self, ti):
        for tre in timeStrings:
            ts,dummy = self.CheckFormat( tre, ti)
            if ts:
                time = getattr(self,timeStrings[tre])(ts)
                dt = DateTime( self.year, self.month, self.day,
                               time.hour, time.minute, time.second, time.microsecond)
                return dt

    #------------------------------------------------------------------------------------------
    def CheckFormat( self, fmt, timeStr):
        """ Check a format against a string. """
        m = re.search(fmt, timeStr)
        if m:
            data = m.group(0)
            leftover = timeStr[len(data)+1:]
            return data, leftover
        else:
            return None, None

    #------------------------------------------------------------------------------------------
    def Split( self, s, delims):
        """ Repeated splits of s until no more delims """
        actDelims = []
        for i in delims:
            if s.count(i) > 0:
                actDelims.append(i)

        ss = [s]
        while actDelims:
            nss = []
            for e in ss:
                ns = e.split(actDelims[0])
                if ns != [e]:
                    nss.extend(ns)
                else:
                    nss.append(e)
            ss = nss[:]
            actDelims = actDelims[1:]
        return ss

    #------------------------------------------------------------------------------------------
    def YMDdateParse( self, date):
        """ Parse a date in y/m/d for 4 or 2 char y format """
        l = self.Split(date, delimiters)
        y  = int( l[0])
        if y < 1980:
            y += 2000
        m  = int( l[1])
        d  = int( l[2])
        try:
            d = datetime.date(y,m,d)
        except ValueError:
            d = datetime.date(y,d,m)
        return d

    #------------------------------------------------------------------------------------------
    def MDYdateParse( self, date):
        """ Parse a date in y/m/d for 4 or 2 char y format """
        l = self.Split(date, delimiters)
        m  = int( l[0])
        d  = int( l[1])
        y  = int( l[2])
        if y < 1980:
            y += 2000
        try:
            d = datetime.date(y,m,d)
        except ValueError:
            d = datetime.date(y,d,m)
        return d

    #------------------------------------------------------------------------------------------
    def ISOtimeParse( self, time):
        l = self.Split( time, ':.')
        h  = int( l[0])
        mi = int( l[1])
        s  = int( l[2])
        if len(l) == 4:
            ms = int( l[3])
        else:
            ms = 0
        return datetime.time( h,mi,s,ms*1000)

    #------------------------------------------------------------------------------------------
    def HRtimeParse( self, time):
        l = self.Split( time, ':.')
        h  = int( l[0])
        mi = int( l[1])
        return datetime.time( h,mi)

    #------------------------------------------------------------------------------------------
    def __add__( self, other):
        if type(other) in (datetime.timedelta, TimeDelta):
            dt = datetime.datetime.__add__(self, other)
            return DateTime(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second,dt.microsecond)
        else:
            td = datetime.datetime.__add__(self, other)
            return TimeDelta( td.days, td.seconds, td.microseconds)

    #------------------------------------------------------------------------------------------
    def __sub__( self, other):
        if type(other) in (datetime.timedelta, TimeDelta):
            dt = datetime.datetime.__sub__(self, other)
            return DateTime(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second,dt.microsecond)
        else:
            print(other, type(other))
            td = datetime.datetime.__sub__(self, other)
            print(td, type(td))
            return TimeDelta( td.days, td.seconds, td.microseconds)

    #------------------------------------------------------------------------------------------
    def __eq__( self, other):
        element = self.GetCompareElement( other)
        return datetime.datetime.__eq__( self, element)

    #------------------------------------------------------------------------------------------
    def __le__( self, other):
        element = self.GetCompareElement( other)
        return datetime.datetime.__le__( self, element)

    #------------------------------------------------------------------------------------------
    def __lt__( self, other):
        element = self.GetCompareElement( other)
        return datetime.datetime.__lt__( self, element)

    #------------------------------------------------------------------------------------------
    def __ge__( self, other):
        element = self.GetCompareElement( other)
        return datetime.datetime.__ge__( self, element)

    #------------------------------------------------------------------------------------------
    def __gt__( self, other):
        element = self.GetCompareElement( other)
        return datetime.datetime.__gt__( self, element)

    #------------------------------------------------------------------------------------------
    def GetCompareElement( self, other):
        oType = type(other)
        if oType in (DateTime,  datetime.datetime):
            return other
        elif oType == datetime.date:
            return DateTime( other.year, other.month, other.day,
                             self.hour, self.minute, self.second, self.microsecond)
        elif oType == datetime.time:
            return DateTime( self.year, self.month, self.day,
                             other.hour, other.minute, other.second, other.microsecond)
        else:
            raise TypeError('Invalid Compare object <%s>' % str(oType))

    #------------------------------------------------------------------------------------------
    def ShowMs( self, flag):
        self.showMS = flag

    #------------------------------------------------------------------------------------------
    def SetDateDiv( self, divItem):
        self.divItem = divItem

    #------------------------------------------------------------------------------------------
    def __str__( self):
        return self.Show()

    #------------------------------------------------------------------------------------------
    def Show( self, fmt=None):
        if fmt == None:
            ds = datetime.datetime.__str__(self)
            self.showMS = getattr( self, 'showMS', False)
            period = ds.find('.')
            if self.showMS:
                if period != -1:
                    ds = ds[:-3]
            elif period != -1:
                ds = ds[:-7]

            self.divItem = getattr( self, 'divItem', '/')
            ds = ds.replace('-', self.divItem)
        elif fmt == 'MDY':
            self.showMS = getattr( self, 'showMS', False)
            if self.showMS:
                ds = '%02d/%02d/%4d %02d:%02d:%02d.%03d' % ( self.month, self.day, self.year,
                                                             self.hour, self.minute, self.second,
                                                             self.microsecond/1000)
            else:
                ds = '%02d/%02d/%4d %02d:%02d:%02d' % ( self.month, self.day, self.year,
                                                        self.hour, self.minute, self.second)
        elif fmt == 'HMS':
            self.showMS = getattr( self, 'showMS', False)
            if self.showMS:
                ds = '%02d:%02d:%02d.%03d' % ( self.hour, self.minute, self.second,
                                               self.microsecond/1000)
            else:
                ds = '%02d:%02d:%02d' % ( self.hour, self.minute, self.second)
        return ds

#----------------------------------------------------------------------------------------------
class TimeDelta( datetime.timedelta):
    #------------------------------------------------------------------------------------------
    def Seconds( self):
        """ Convert a time delta into seconds. """
        days = self.days * (24 * 3600)
        seconds = self.seconds
        microseconds = self.microseconds / 1000000.0
        return days + seconds + microseconds

    #------------------------------------------------------------------------------------------
    def __div__( self, v):
        """ Display a timedelta string with the micorseconds hidden """
        td = datetime.timedelta.__div__(self, v)
        return TimeDelta( td.days, td.seconds, td.microseconds)

    #------------------------------------------------------------------------------------------
    def __mul__( self, v):
        """ Display a timedelta string with the micorseconds hidden """
        td = datetime.timedelta.__mul__(self, v)
        return TimeDelta( td.days, td.seconds, td.microseconds)

    #------------------------------------------------------------------------------------------
    def ShowMs( self, flag):
        self.showMS = flag

    #------------------------------------------------------------------------------------------
    def __str__( self):
        """ Display a timedelta string with the micorseconds hidden """
        td = datetime.timedelta.__str__(self)
        self.showMS = getattr( self, 'showMS', False)
        period = td.find('.')
        if self.showMS:
            if period != -1:
                td = td[:-3]
        elif period != -1:
            td = td[:-7]

        return td

#----------------------------------------------------------------------------------------------
if __name__ == '__main__':
    d = DateTime.today()
    d1 = d.SetTime('0:00:10.430')

    d = DateTime(2005,12,25,12,1,2,123456)
    d = d.Set('11/12/2005 01:12:32.987')
    print(d)
    d = d.Set('1/2/2003 01:02:03')
    print(d)
    d1 = DateTime(2005,1,1)
    d2 = DateTime(2005,1,5)
    td = d2 - d1
    td
    print(td)


