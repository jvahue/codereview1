"""
Lint Clean Up

1. Put a header on the file
2. Go through the LINT o/p file and remove anything that starts with ---
   (i.e. Module Names, Global Clean Up, etc.
3. Remove blank lines
4. Remove full path name and make it subdir/filename
"""
import csv
import os
import sys

# turn this off when done debugging
_debug = True

def CleanUp( fn):
    print '\nCleanup %s\n' % fn
    f = open( fn, 'rb')
    csvIn = csv.reader( f)
    
    # debug?
    if _debug:
        fno = os.path.splitext( fn)[0] + '_1.csv'
    else:
        fno = fn
    fo = open( fno, 'wb')
    csvOut = csv.writer(fo)
         
    csvOut.writerow(['Cnt','Filename','Function','Line','Type','ErrNo','Description'])
    
    lineNum = 0
    for l in csvIn:
        lineNum += 1
        if len( l) > 0:
            if l[0].find('---') == -1:
                if len(l) != 6:# and l[1:6] == l[6:]:
                    l = l[:6]
                    
                # remove full pathname
                if l[0] and l[0][0] != '.':
                    path, fn = os.path.split(l[0])
                    subdir = os.path.split( path)[1]
                    l = [r'%s\%s' % (subdir, fn)] + l[1:]
                    
                opv = [1] + l
                csvOut.writerow(opv)
            else:
                print 'Delete[%4d]: %s' % (lineNum, ','.join(l))
        else:
            print 'Delete[%4d]: Blank Line' % ( lineNum)

    fo.close()
    
    
    
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "\n\nERROR:\nUsage: CleanLint <filename>"
    else:
        CleanUp( sys.argv[1])