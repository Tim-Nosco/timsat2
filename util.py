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
    def __repr__(self):
        return self.name
    def value(self):
        return None if not self.stk_ptr else self.stk_ptr.val
    def assign(self,stk_ptr):
        assert(isinstance(stk_ptr,Assignment))
        self.stk_ptr = stk_ptr
    def unassign(self):
        self.stk_ptr = None

class Literal:
    #A literal contains a reference to a variable and a polarity
    # bool(polarity)==True means the literal is +variable
    # bool(polarity)==False means the literal is -variable
    def __init__(self,variable,polarity):
        self.variable = variable
        self.polarity = polarity
    def __hash__(self):
        i = id(self.variable)
        return i if self.polarity else -i
    def __repr__(self):
        return "{}{}".format("" if self.polarity else "-",self.variable)
    def __neg__(self):
        return Literal(self.variable, not self.polarity)

class Clause:
    #A clause contains:
    #1) a set of literals
    #2) two watch pointers
    #for watch pointers to work, there must be at least two literals
    def __init__(self,*literals):
        self.literals = literals
        if len(literals)>1:
            self.wp1 = literals[0]
            self.wp2 = literals[1]
        
