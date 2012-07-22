"""
This file holds an object that verifies format information.  That is for functions
or files or whatever set of lines you want to check, this class will see if you set
of lines matches the sequecen and content of a description of those lines.

The description holds important items you want to see in the lines in the order that
you want to see them.

The class also understands and trackes key words that you passed in and can tell you
things about them, like where was the keyword item found in the real lines, and where
did it end.

For example if the Keyword was <TheParameters> and the function header was being
checked, it could tell you that the parameters started on line x and end on line y
Or if the keyword was <TheLocalFunctions> where was that keyword in the file
"""
#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
from collections import OrderedDict

import re

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
from utils.util import Holder

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eAnyText = '.*?'
ePosDef = r'(:[0-9]+:|:D:)$'

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------
class Item( Holder):
    """ This holds the info about an item (or a group of items that go together).  It allows for
        checking the existence of the item in the line buffer.
    """
    def __init__( self, raw, desc, dependsOn = None):
        self.raw = [raw]
        self.desc = [desc]
        self.offset = [0]
        self.span = 1    # how many lines does this item span
        self.index = -1  # what line in the file did we find this
        self.keywords = OrderedDict()
        self.dependsOn = dependsOn

    #-----------------------------------------------------------------------------------------------
    def AddGroupItem( self, raw, desc, span):
        self.raw.append( raw)
        self.desc.append(desc)
        self.span += span
        offset = span - 1
        self.offset.append( offset)

    #-----------------------------------------------------------------------------------------------
    def Reset( self):
        self.index = -1
        for k in self.keywords:
            h = self.keywords[k]
            h.line0 = -1
            h.lines = []

    #-----------------------------------------------------------------------------------------------
    def Keywords( self):
        keyRe = re.compile( r'<[A-Z][A-Za-z0-9_]+>')

        newDesc = []
        for i in self.desc:
            key = keyRe.findall( i)
            for keyword in key:
                # remove keyword from desc Item - needed when something expected after the keyword
                i = i.replace( keyword, eAnyText).strip()

                if keyword not in self.keywords:
                    self.keywords[keyword] = Holder( line0 = -1, lines=[])
            newDesc.append(i)

        self.desc = newDesc

    #-----------------------------------------------------------------------------------------------
    def IsEmptyDesc( self):
        """ see if all the descriptions are equal to eAnyText """
        isEmpty = True
        for i in self.desc:
            if i != eAnyText:
                isEmpty = False
                break
        return isEmpty

    #-----------------------------------------------------------------------------------------------
    def JoinRaw( self):
        return '\n'.join( self.raw)

    #-----------------------------------------------------------------------------------------------
    def MatchBuffer( self, lineCount, maxSpan, lineBuffer):
        """ start at the top of the buffer and see if we match all we need """
        if self.index == -1 and len(lineBuffer) >= self.span:
            lbx = 0
            isMatch = True
            for ix, desc in enumerate(self.desc):
                lbx += self.offset[ix]
                bufLine = lineBuffer[ix+lbx].strip()

                try:
                    descLineRe = re.compile( desc, re.DOTALL)
                except:
                    raise
                m = descLineRe.search( bufLine)
                if not m:
                    isMatch = False
                    break

            if isMatch:
                if self.dependsOn is None or self.dependsOn.index != -1:
                    self.index = (lineCount - maxSpan) + 1
                else:
                    isMatch = False
        else:
            isMatch = False

        return isMatch

#---------------------------------------------------------------------------------------------------
class FormatChecker:
    def __init__( self, detector, updateTime, desc, rawDesc):
        """ desc - the string of lines describing the format
            lines followed by a :#: indicate how many lines after the previous descLine it can be
            in the actual file, this allows defining grouping
            NEW: groups are looked for together as a block or group or flock or chunck or ...
        """
        posDefRe = re.compile( ePosDef)

        self.detector = detector
        self.updateTime = updateTime
        self.desc = desc
        dl = desc.split('\n')
        self.descLines = [i.strip() for i in dl if i.strip()]
        dl = rawDesc.split('\n')
        self.rawDescLines = [i for i in dl if i.strip()]

        self.items = []
        for ix, i in enumerate(self.descLines):
            posDef = posDefRe.findall( i.strip())
            if posDef:
                posDef = posDef[0]
                if posDef == ':D:':
                    descLine = self.descLines[ix].replace( posDef, '').strip()
                    item = Item( self.rawDescLines[ix], descLine, self.items[-1])
                    self.items.append(item)
                else:
                    span = int(posDef.replace(':', ''))
                    item = self.items[-1]
                    descLine = self.descLines[ix].replace( posDef, '').strip()
                    item.AddGroupItem( self.rawDescLines[ix], descLine, span)
            else:
                item = Item( self.rawDescLines[ix], self.descLines[ix])
                self.items.append(item)

        # find out how big our line buffer needs to be
        maxSpan = [i.span for i in self.items]
        if maxSpan:
            maxSpan.sort()
            self.maxSpan = maxSpan[-1]
        else:
            self.maxSpan = 1

        self.lineBuffer = []

        self.lineCount = 0

        # find lineSpan limits for a line of keywords in the description items
        for item in self.items:
            item.Keywords()

        # move empty item's keywords to the item before them, and dependers too
        for ix, item in enumerate( self.items):
            if item.IsEmptyDesc():
                if ix == 0:
                    # move keywords forward special case
                    self.items[1].keywords.update( item.keywords)
                else:
                    # move it back one item
                    self.items[ix-1].keywords.update( item.keywords)

        # clear out the empty descriptors
        self.items = [i for i in self.items if not i.IsEmptyDesc()]

    #-----------------------------------------------------------------------------------------------
    def GetKeywordItems( self, keyword):
        keyItems = [item for item in self.items if keyword in item.keywords]
        return keyItems

    #-----------------------------------------------------------------------------------------------
    def Check( self, lines):
        """ Scan these lines versus the expected items and sequence collecting data on any keywords
        """
        if type( lines) == str:
            lines = lines.split('\n')

        self.lines = lines

        for lx,line in enumerate(lines):
            self.CheckLine( lx, line)

    #-----------------------------------------------------------------------------------------------
    def CheckLine( self, lx, line):
        """ Check a single line, this function allows someone running the file by line to check
            format as it does it.
        """
        if lx == 0:
            self.Reset()

        lx += 1 # start numbering from 1 vs. 0
        if lx > self.lineCount:
            self.lineCount = lx

        lineStrip = line.strip()
        self.lineBuffer.append(lineStrip)
        if len(self.lineBuffer) == self.maxSpan or self.bufferSizeMet:
            self.bufferSizeMet = True
            self.BufferCheck(lx, line)

    #-----------------------------------------------------------------------------------------------
    def BufferCheck( self, lx, line):
        # now that we have the line buffer filled
        # lets scan through our items for matchs
        for ix, item in enumerate(self.items):
            if item.MatchBuffer( lx, self.maxSpan, self.lineBuffer):
                # only assign this to one item and start at the top
                self.InitKeyword( item, lx-self.maxSpan, line)
                break
        else:
            # collecting info for an open keyword
            self.SaveKeyWordData( line)

        # toss out the oldest
        self.lineBuffer = self.lineBuffer[1:]

    #-----------------------------------------------------------------------------------------------
    def FinishBuffer( self):
        """ This funciton makes sure the line buffer is empty to ensure all lines in the text
            have been check for a match
        """
        bLen = len(self.lineBuffer)

        while self.lineBuffer:
            self.BufferCheck(self.lineCount+1, '')
            self.lineCount += 1

        self.lineCount -= bLen

    #-----------------------------------------------------------------------------------------------
    def Reset( self):
        """ Start a new check session """
        # keep the location each item is found at
        for i in self.items:
            i.Reset()

        self.activeItem = None
        self.lineCount = 0
        self.bufferSizeMet = False

    #-----------------------------------------------------------------------------------------------
    def InitKeyword( self, item, lx, line):
        """ scan our keywords and init an entry
        """
        self.activeItem = None

        for keyword in item.keywords:
            item.keywords[keyword].line0 = lx
            item.keywords[keyword].lines = self.lineBuffer[:item.span]
            self.activeItem = item

    #-----------------------------------------------------------------------------------------------
    def SaveKeyWordData( self, line):
        if self.activeItem:
            for keyword in self.activeItem.keywords:
                self.activeItem.keywords[keyword].lines.append(line)

    #-----------------------------------------------------------------------------------------------
    def ReportErrors( self, db, rpfn, lineNum, checkDesc, func, errMsg):
        """ Report the errors detected during the scan
            Item Position Relative line spans met
            All items present
            Item Sequence is as expected
        """
        # verify all the items where present and in the right order
        found = []
        for ix,item in enumerate(self.items):
            if item.index != -1:
                found.append( item)
            else:
                severity = 'Error'
                violationId = errMsg + '-MissingItem'
                lineMis = lineNum
                rawText = item.JoinRaw()
                desc = '%s\n%s[Item %d]\nmissing in %s' % (checkDesc, rawText, ix, func )
                details = '%s[Item %d]\nnot found in %d possible lines' % (rawText, ix, self.lineCount)
                db.Insert(rpfn, func, severity, violationId, desc,
                          details, lineMis, self.detector, self.updateTime)

        # report items out of sequence in the header
        expectSeq = found[:]
        foundItems = len(found)
        found.sort( key=lambda x: x.index)
        ordSave = [item.desc for item in found]
        itemSeq = ordSave[:]

        for ix, item in enumerate(expectSeq):
            if itemSeq and item.desc != itemSeq[0]:
                itemSeq.remove( item.desc)

                # get original pos/count
                for opx, opi in enumerate(self.items):
                    if opi.desc == item.desc:
                        break
                expPc = '%d/%d' % (opx, len(self.items))

                # find in it our actual data
                for apx, api in enumerate(ordSave):
                    if api == item.desc:
                        break
                actPc = '%d/%d' % (apx, len(ordSave))

                # header field order
                severity = 'Warning'
                violationId = errMsg + '-Seq'
                lineSeq = item.index
                rawText = item.JoinRaw()
                desc = '%s Sequence Error\n%s[Item %d]' % (checkDesc, rawText, ix)
                msgStr = '%s[Item %d]\nexpected position %s found in position %s (line %d)'
                details = msgStr % (rawText, ix, expPc, actPc, item.index)
                db.Insert(rpfn, func, severity, violationId, desc,
                          details, lineSeq, self.detector, self.updateTime)
            else:
                itemSeq = itemSeq[1:]

#===================================================================================================
if __name__ == '__main__':
    import datetime
    import ProjFile as PF
    import os
    import ViolationDb

    #projFile = r'C:\Users\P916214\Documents\Knowlogic\CodeReviewProj\FAST\G4.crp'
    projFile = r'C:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ\G4.crp'
    pf = PF.ProjectFile(projFile)
    vDb = ViolationDb.ViolationDb( pf.paths[PF.ePathProject])

    fpfn = pf.FullPathName( 'TrendUserTables.c')
    if fpfn:
        fpfn = fpfn[0]

        lines = pf.GetFileContents( fpfn)

        # determine file type c/h
        ext = os.path.splitext( fpfn)[1]
        # build format name
        fmtName = 'File_%s' % ext.replace('.','').upper()
        fileDescLines = pf.formats.get( fmtName, '')
        rawDescLines = pf.rawFormats.get( fmtName, '')

        updateTime = datetime.datetime.today()

        fc = FormatChecker( 'test', updateTime, fileDescLines, rawDescLines)
        for x,l in enumerate(lines):
            fc.CheckLine(x,l)

        fc.FinishBuffer()

        #fc.Check( lines)

        rpfn, title = pf.RelativePathName( fpfn)

        fc.ReportErrors( vDb, rpfn, -1, 'File Format', title, 'FileFmt')
        vDb.Commit()
