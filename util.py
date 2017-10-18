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
        self.literals = literals
        self.s = set(literals)
        if len(literals)>1:
            self.refA = 0 #literals[0]
            self.refB = 1 #literals[1]
    def __repr__(self):
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
        return self.literals
    def status(self):
        #this function determines if the clause is:
        #1) UNSAT
        #2) UNIT
        #3) SAT
        #4) UNRESOLVED
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
                if i!=known and self.literals[i].value()==None:
                    if known==self.refA:
                        self.refB = i
                    else:
                        self.refA = i
                    #adjust occurrence list
                    lit_to_remove = self.literals[other]
                    lit_to_add = self.literals[i]
                    lit_to_remove.occurrence_unlink(self)
                    lit_to_add.occurrence_link(self)           
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
        l = self.s.union(clause2.s)
        f = filter(lambda x: -x in l, l)
        #a single literal must differ (no more or less)
        assert(len(f)==2)#+/- x
        for x in f:
            l.remove(x)
        return Clause(*l)

class OccurrenceList(list):
    def unlink(self,idx):
        return self[:idx]+self[idx+1:]
