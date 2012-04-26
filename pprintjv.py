
class PPrinter:
    def __init__( self, f = None, sep = ' ', indent = ''):
        self.f = f
        self.sep = sep
        self.indent = indent
        
    def SmartPrint(self, d, NL=True):
        theType = type(d)
        if theType == list or theType == tuple:
            for i in d:
                self.SmartPrint(i, False)
            s = ''
        elif theType == dict:
            k = d.keys()
            k.sort()
            for i in k:
                self.SmartPrint(d[i])
            s = ''
        elif theType == float:
            s = '%s%.2f' % (self.indent, d)
        else:
            s = '%s%s' % (self.indent, str(d))
            
        if self.f:
            if NL: nl = '\n'
            else: nl = ''
            self.f.write(s + self.sep + nl)
        else:    
            if NL:
                print s
            else:
                print s,
                
def Show( d, oneLine = False, f=None, sep=' ', indent = ''):
    ft = type(f)
    if ft == str:
        af = file(f,'w')
    else:
        af = f
        
    pp = PPrinter( af, sep, indent)
    
    for i in d:
        pp.SmartPrint( i, not oneLine)

    if oneLine:
        if af: af.write('\n')
        else: print 
        
    if ft == str:
        af.close()
    
sh = Show

