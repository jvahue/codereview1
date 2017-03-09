#!/usr/bin/env python
#coding:utf-8
"""
Filename: PatchDB.py

Description: This file can be used as a frame to change the contents of a field in the DB.  For
instance if the DB holds file names like 'code\%' and you want to strip 'code\' of the front of
each file name the basics of this script can be used.

Author:  Jeff Vahue --<jvahue@knowlogicsoftware.com>
Created: 3/9/2017

This document is the property of Knowlogic Software Corp. (KLGC). You may not possess, use,
copy or disclose this document or any information in it, for any purpose, including without
limitation to design, manufacture, or repair parts, or obtain FAA or other government approval to
do so, without KLGC's express written permission. Neither receipt nor possession of this document
alone, from any source, constitutes such permission. Possession, use, copying or disclosure by
anyone without KLGC's express written permission is not authorized and may result in criminal and/or
civil liability.

WARNING -- This document contains technical data the export of which is or may be restricted by the
Export Administration Act and the Export Administration Regulations (EAR), 15 C.F.R. parts 730-774.
Diversion contrary to U.S. law is prohibited.  The export, re-export, transfer or re-transfer of
this technical data to any other company, entity, person, or destination, or for any use or purpose
other than that for which the technical data was originally provided by P&W, is prohibited without
prior written approval from P&W and authorization under applicable export control laws.

EAR Export Classification:  9E991
"""

#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
import os

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Library
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
import ViolationDb

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
projRoot = r'C:\knowlogic\tools\CRP_Test\fix'

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------
def PatchFileName():
    """ Replace all filenames with 'code\\*' in them with just '*'
    """
    if not os.path.isdir(projRoot):
        print('Unknown root <%s>' % projRoot)
        raise ValueError

    db = ViolationDb.ViolationDb(projRoot)

    s = """
    select rowId, filename
    from violations
    where filename like 'code\%'"""
    q = db.Query(s)

    print('%d rows with code in filename' % len(q))

    for row in q:
        newName = row.filename.replace('code\\', '')
        s = "update violations set filename=? where rowId=?"
        db.Execute(s, newName, row.rowId)

    db.Commit()

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    PatchFileName()
