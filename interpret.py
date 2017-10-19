from util import Variable, Literal, Clause
import re,logging

class Parser:
    #takes a string of clauses separated by newlines
    def __init__(self,filename=None,lines=None):
        #choose one or the other, a file or direct input
        assert(bool(filename)^bool(lines))
        if filename:
            with open(filename,'r') as f:
                lines = f.read()    
        self.clauses = self.interpret(lines)
    def interpret(self,lines):
        regx = re.compile(r"(-?)(\d+)")
        self.known = dict()
        clauses = []
        c = []
        m = re.match("p (.+) (.+)\s*\n",lines)
        checksum = m.groups() if m else None
        
        lines = re.sub("[cp].*?\n","",lines)
        for literal in re.split(r"[\s\n]+",lines):
            m = re.match(regx,literal)
            if m:
                varname = m.group(2)
                if varname != "0":
                    var = self.known.get(varname,Variable(varname))
                    var.count+=1
                    self.known[varname]=var
                    l = Literal(var,not bool(m.group(1)))
                    c.append(l)
                else:
                    addition = Clause(*c)
                    addition.link()
                    clauses.append(addition)
                    c = []
        if checksum:
            assert(len(self.known)==int(checksum[0]))
            assert(len(clauses)==int(checksum[1]))
        return clauses

if __name__=="__main__":
    import sys
    from solver import Solver
    if len(sys.argv)<2:
        exit(1)
    #logging.basicConfig(filename=sys.argv[1]+".log",level=logging.DEBUG)
    #logging.basicConfig(level=logging.DEBUG)
    p = Parser(sys.argv[1])
    s = Solver(p)
    print "Solving..."
    r = s.CDCL()
    if r=="SAT":
        print r
        print s.Model()
    else:
        print "UNSAT"
