__author__ = 'p916214'

import csv

from utils.DB.sqlLite import database


dbName = r'C:\Users\P916214\Documents\Knowlogic\CodeReviewProj\KsCrDb.db'

paths = (
    (r'C:\ghs\multi506\ansi', '<incRoot>'),
    (r'D:\FAST\dev\cp\G4_CP', '<srcRoot>'),
)

def CleanUp():
    db = database.DB_SQLite()
    db.Connect(dbName)

    # clean path information
    s = '''select rowId,description
           from violations
           where
           status is not null'''
    data = db.Query( s)
    u = 'update violations set description=? where rowId = ?'
    for i in data:
        desc0 = i.description
        desc = CleanFpfn( i.description)
        if desc0 != desc:
            db.Execute( u, desc, i.rowId)

    db.Commit()

    # clean Metric.File length
    s = "select rowId, description, details from violations where violationId = 'Metric.File'"
    data = db.Query( s)
    u = 'Update violations set description=?, details=? where rowId=?'

    for i in data:
        desc = i.description + ' total lines 2001'
        dets = 'Total line count exceeds project maximum 2000'
        db.Execute( u, desc, dets, i.rowId)

    db.Commit()

    db.Close()

#-----------------------------------------------------------------------------------------------
def CleanFpfn( desc):
    """ This function cleans out any full path file names and creates relative path file names
        for names in the description.

        PC-Lint precedes file names with 'file' and 'module' in its descriptions
        e.g.,
        [Reference: file D:\knowlogic\FAST\dev\CP\drivers\FPGA.c: line 559]
        (line 62, file D:\knowlogic\FAST\dev\CP\drivers\RTC.c)
        (line 61, file <path>\drivers\EvaluatorInterface.h, module <path>\application\AircraftConfigMgr.c)
    """
    debug = False
    desc0 = desc

    # compute the relative path from a srcRoot
    for sr, thePattern in paths:
        srl = sr.lower()
        # replace all paths in the description
        while True:
            dl = desc.lower()
            at = dl.find( srl)
            if at != -1:
                end = at + len(srl)
                desc = desc[0:at] + thePattern + desc[end:]
            else:
                break

    if debug and desc0 != desc:
        print( 'Was: %s\n Is:%s' %  (desc0, desc))

    return desc

if __name__ == '__main__':
    CleanUp()