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

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------
class Item( Holder):
    def __init__( self, raw, desc):
        self.raw = raw
        self.desc = desc
        self.index = -1
        self.span = -1
        self.keywords = OrderedDict()

    def Reset( self):
        self.index = -1
        for k in self.keywords:
            h = self.keywords[k]
            h.line0 = -1
            h.lines = []

class FormatChecker:
    def __init__( self, detector, updateTime, desc, rawDesc):
        """ desc - the string of lines describing the format
            lines followed by a :#: indicate how many lines after the previous descLine it can be
            in the actual file, this allows defining grouping
        """
        eAnyText = '.*?'

        self.detector = detector
        self.updateTime = updateTime
        self.desc = desc
        dl = desc.split('\n')
        self.descLines = [i.strip() for i in dl if i.strip()]
        dl = rawDesc.split('\n')
        self.rawDescLines = [i.strip() for i in dl if i.strip()]

        self.items = []
        for ix, i in enumerate(self.descLines):
            item = Item( self.rawDescLines[ix], self.descLines[ix])
            self.items.append(item)

        self.lineCount = 0

        posRe = re.compile( r':[0-9]+:')
        keyRe = re.compile( r'<[A-Z][A-Za-z0-9_]+>')

        # find lineSpan limits for a line of keywords in the description items
        for ix,item in enumerate(self.items):
            span = -1
            # check for positional information
            isPos = posRe.findall( item.desc)
            if isPos:
                # get index
                span = int(isPos[0].replace( ':',''))
                # remove it
                item.desc = item.desc.replace( isPos[0], '').strip()
            item.span = span

            # check for keywords
            key = keyRe.findall( item.desc)
            for keyword in key:
                # remove keyword from desc Item - needed when something expected after the keyword
                item.desc = item.desc.replace( keyword, eAnyText).strip()

                if keyword not in item.keywords:
                    item.keywords[keyword] = Holder( line0 = -1, lines=[])

        # move their keywords to the item before them
        for ix, item in enumerate( self.items):
            if item.desc == eAnyText:
                if ix == 0:
                    # move keywords forward special case
                    self.items[1].keywords.update( item.keywords)
                else:
                    # move it back one item
                    self.items[ix-1].keywords.update( item.keywords)

        # clear out the empty descriptors
        self.items = [i for i in self.items if i.desc and i.desc != eAnyText]

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
            self.CheckInit()

        lx += 1 # start numberinf from 1 vs. 0
        if lx > self.lineCount:
            self.lineCount = lx

        lineStrip = line.strip()
        if lineStrip:
            for ix, item in enumerate(self.items):
                # have we seen this line already?
                if item.index == -1:
                    try:
                        descLineRe = re.compile( item.desc, re.DOTALL)
                    except:
                        raise
                    m = descLineRe.search( lineStrip)
                    if m:
                        item.index = lx
                        self.InitKeyword( item, lx, line)
                        break
            else:
                # collecting info for an open keyword
                self.SaveKeyWordData( line)

    #-----------------------------------------------------------------------------------------------
    def CheckInit( self):
        """ Start a new check session """
        # keep the location each item is found at
        for i in self.items:
            i.Reset()

        self.activeItem = None

    #-----------------------------------------------------------------------------------------------
    def InitKeyword( self, item, lx, line):
        """ scan our keywords and init an entry
        """
        self.activeItem = None

        for keyword in item.keywords:
            item.keywords[keyword].line0 = lx
            item.keywords[keyword].lines = [line]
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
        # verify all the items offsets were met
        for ix, item in enumerate( self.items):
            offset = item.span
            index = item.index
            x1 = ix - 1
            # if we have positional info and we found the line
            if offset != -1 and index != -1:
                if (self.items[x1].index + offset) != index:
                    # positional error
                    severity = 'Error'
                    violationId = errMsg + '-Position'
                    linePos = index
                    delta = abs(index - self.items[x1].index)
                    desc = '%s <%s> [%d]\nposition relative to\n<%s> [%d]' % (checkDesc,
                                                                              item.raw,
                                                                              ix,self.items[x1].raw, x1)
                    msgStr = "A: <%s>[%d]\nis not %d line%s after\nB: <%s>[%d]\nLine Delta(A:%d/B:%d): %d"
                    details = msgStr % (
                        item.raw, ix,
                        offset,
                        '' if offset == 1 else 's',
                        self.items[x1].raw, x1,
                        index, self.items[x1].index,
                        delta)
                    db.Insert(rpfn, func, severity, violationId, desc,
                              details, linePos, self.detector, self.updateTime)

        # verify all the items where present and in the right order
        found = []
        for ix,item in enumerate(self.items):
            if item.index != -1:
                found.append( item)
            else:
                severity = 'Error'
                violationId = errMsg + '-MissingField'
                lineMis = -1
                desc = '%s <%s>[%d] missing in\n<%s>' % (checkDesc, item.raw, ix, func )
                details = '<%s>[%d] not found in %d possible lines' % (item.raw, ix, self.lineCount)
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
                severity = 'Error'
                violationId = errMsg + '-Seq'
                lineSeq = item.index
                desc = '%s Sequence Error\n<%s>[%d]' % (checkDesc, item.raw, ix)
                msgStr = '<%s>[%d]\nexpected position %s found in position %s (line %d)'
                details = msgStr % (item.raw, ix, expPc, actPc, item.index)
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

    projFile = r'C:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ\G4.crp'
    pf = PF.ProjectFile(projFile)
    vDb = ViolationDb.ViolationDb( pf.paths[PF.ePathProject])

    fpfn = pf.FullPathName( 'AircraftConfigMgr.c')
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
        fc.Check( lines)

        rpfn, title = pf.RelativePathName( fpfn)

        fc.ReportErrors( vDb, rpfn, -1, 'File Format', title, 'FileFmt')
        vDb.Commit()
