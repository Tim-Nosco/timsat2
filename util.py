class Assignment:
    #each value in the assignment stack is a struct:
    #1) the decision level: Int
    #2) the variable: *Variable
    #3) the value: Bool
    #4) the clause(if applicable): Clause or None
    def __init__(self,dl,var,val,clause):
        self.dl = dl
        self.var = var
        self.val = val
        self.clause = clause

class AssignmentStack(list):
    #This stack holds Assignment objects
    push = list.append

class Variable:
    #A variable's value is stored in the assignment stack
    def __init__(self,name):
        self.stk_ptr = None
        self.name = name
        self.count = 0
        self.waiting = False
        #there is an occurance list for each polarity
        self.occurrence={True:OccurrenceList(),False:OccurrenceList()}
    def __repr__(self):
        return self.name
    def value(self):
        return None if not self.stk_ptr else self.stk_ptr.val
    def assign(self,stk_ptr):
        assert(isinstance(stk_ptr,Assignment))
        self.stk_ptr = stk_ptr
    def unassign(self):
        self.stk_ptr = None
    def isAssigned(self):
        return self.stk_ptr != None

class Literal:
    #A literal contains a reference to a variable and a polarity
    # bool(polarity)==True means the literal is +variable
    # bool(polarity)==False means the literal is -variable
    def __init__(self,variable,polarity=True):
        self.variable = variable
        self.polarity = polarity
    def __hash__(self):
        i = id(self.variable)
        return i if self.polarity else -i
    def __repr__(self):
        return "{}{}".format("" if self.polarity else "-",self.variable)
    def __neg__(self):
        return Literal(self.variable, not self.polarity)
    def value(self):
        v = self.variable.value()
        if v==None:
            return v
        else:
            return v if self.polarity else (not v)
    def __eq__(self,x):
        return hash(self)==hash(x)
    def occurrence_link(self,clause):
        self.occurrence().append(clause)
    def occurrence_unlink(self,clause):
        l = self.occurrence()
        l = l.unlink(l.index(clause))
        self.variable.occurrence[self.polarity] = l
    def occurrence(self):
        return self.variable.occurrence[self.polarity]

class Clause:
    #A clause contains:
    #1) a set of literals
    #2) two watch pointers
    #for watch pointers to work, there must be at least two literals
    def __init__(self,*literals):
        self.s = set(literals)
        #setup the watch pointers
        self.literals = literals
        first = (-1,0)
        second = (-1,0)
        self.max_lit = None
        m=-1
        for i, l in enumerate(self.literals):
            if l.variable.stk_ptr:
                dl = l.variable.stk_ptr.dl
                if dl >= first[1]:
                    second = first
                    first = (i,dl)
                if dl>m and l.variable.stk_ptr.clause:
                    m = dl
                    self.max_lit = l
        if len(literals)>1:
            self.refA = first[0] if first[0] != -1 else 0
            self.refB = second[0] if second[0] != -1 else ((self.refA + 1) % len(self.literals))
    def link(self):
        if len(self.literals)>1:
            self.literals[self.refA].occurrence_link(self)
            self.literals[self.refB].occurrence_link(self)
    def __repr__(self):
        if len(self.literals)>1:
            #print stars by the watched literals
            s = []
            for i,l in enumerate(self.literals):
                t = "*" if i==self.refA or i==self.refB else ""
                s.append(t+str(l))
            return "[{}]".format(', '.join(s))
        else:
            return str(self.literals) 
    def __len__(self):
        return len(self.literals)
    def __eq__(self,x):
        if isinstance(x,Clause):
            return self.s==x.s
        else:
            return False
    def __contains__(self,x):
        return x in self.s
    def __iter__(self):
        return iter(self.literals)
    def status(self):
        #this function determines if the clause is:
        #1) UNSAT
        #2) UNIT
        #3) SAT
        #4) UNRESOLVED
        #it maintains two watch pointers (pointers to literals)
        # these watch pointers help limit the time required to determine
        # the clause's status
        if len(self.literals)<1:
            #the empty clause is always unsat
            return "UNSAT"
        elif len(self.literals)==1:
            #a single literal clause
            v = self.literals[0].value()
            if v==None:
                self.unitLiteral = self.literals[0]
                return "UNIT"
            elif v:
                return "SAT"
            else:
                return "UNSAT"
        vA = self.literals[self.refA].value()
        vB = self.literals[self.refB].value()
        if vA or vB:
            #a single true literal makes the clause sat
            return "SAT"
        elif (vA==False) and (vB==False):
            return "UNSAT"
        elif ((vA==False)^(vB==False)) and ((vA==None)^(vB==None)):
            #one literal is false, the other is unassigned
            # we must ensure there are no other unassigned literals
            # in order to conclude unit
            known,other = (self.refA,self.refB) if vA==None else (self.refB, self.refA)
            for i in range(len(self.literals)):
                if (i!=known and self.literals[i].value()==None) or (self.literals[i].value()):
                    if known==self.refA:
                        self.refB = i
                    else:
                        self.refA = i
                    #adjust occurrence list
                    lit_to_remove = self.literals[other]
                    lit_to_add = self.literals[i]
                    lit_to_remove.occurrence_unlink(self)
                    lit_to_add.occurrence_link(self)
                    if self.literals[i].value():
                        return "SAT"
                    break
            else:
                #no other literals were unassigned
                self.unitLiteral = self.literals[known]
                return "UNIT"
        return "UNRESOLVED"
    def resolve(self,clause2):
        #this function takes two clauses 
        # that differ by a single literal
        # and resolves them into a single clause
        #resolution only works on two clauses
        assert(isinstance(clause2,Clause))
        all_literals = self.s.union(clause2.s)
        shared_var = filter(lambda x: -x in all_literals, all_literals)
        #a single literal must differ (no more or less)
        assert(len(shared_var)==2)#+/- x
        for x in shared_var:
            all_literals.remove(x)
        return Clause(*all_literals)

class OccurrenceList(list):
    def unlink(self,idx):
        return OccurrenceList(self[:idx]+self[idx+1:])
