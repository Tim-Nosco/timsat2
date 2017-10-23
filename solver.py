from util import Assignment, AssignmentStack, Variable, Literal, Clause
import logging

class Solver:
    def __init__(self,parser):
        self.vars = [parser.known[x] for x in parser.known]
        self.vars.sort(key=lambda x: x.count)
        self.clauses = parser.clauses
        self.setup()
    def setup(self):
        for v in self.vars:
            v.unassign()
        self.dl = 0
        self.stack = AssignmentStack()
        self.pre_condition_CONFLICT=False
        for clause in self.clauses:
            #check for single variable or empty clauses (unsat or unit)
            s = clause.status()
            if s == "UNSAT":
                logging.info("pre_condition: Found UNSAT clause: %s",clause)
                self.pre_condition_CONFLICT = True
                break
            elif s == "UNIT":
                #single literal clause
                logging.debug("pre_condition: Single literal clause: %s",clause)
                #add assignment to stack
                literal = clause.literals[0]
                a = Assignment(0,literal.variable,literal.polarity,clause)
                logging.info("Learned: %s -> %s = %s",clause,literal.variable,literal.polarity)
                self.stack.push(a)
                if self.UnitPropagation():
                    self.pre_condition_CONFLICT = True
                    break
    def Model(self):
        return dict((v.name,v.value()) for v in self.vars)
    def PickBranchingVariable(self):
        for v in self.vars:
            if not v.isAssigned():
                logging.info("Branching dl: %s -> %s = %s",self.dl+1,v.name,False)
                return v,False
    def AllVariablesAssigned(self):
        return all(x.isAssigned() for x in self.vars)
    def UnitPropagation(self):
        if len(self.stack)<=0:
            return False
        current = len(self.stack)-1
        while current < len(self.stack):
            a = self.stack[current]
            a.var.assign(a)
            a.var.waiting = False
            for clause in a.var.occurrence[not a.val]:
                case = clause.status()
                logging.debug("Clause: %s\n Case: %s",clause,case)
                if case=="UNSAT":
                    logging.info("Conflict on clause: %s",clause)
                    return a,clause
                elif case=="UNIT":
                    l = clause.unitLiteral
                    if not l.variable.waiting:
                        new_assignment = Assignment(self.dl,l.variable,l.polarity,clause)
                        self.stack.push(new_assignment)
                        l.variable.waiting = new_assignment
                        logging.info("Learned: %s -> %s = %s",clause,l.variable.name,l.polarity)
                    else:
                        #the variable hasn't been assigned yet because it was determined from a
                        # unit clause in this same loop
                        # there could be a conflict, so we must check before continuing
                        l.variable.assign(l.variable.waiting)
                        case = clause.status()
                        if case=="UNSAT":
                            logging.info("Conflict on clause: %s",clause)
                            return l.variable.waiting,clause
                        else:
                            l.variable.unassign()
            current += 1
    def ConflictAnalysis(self,conflict):
        assignment,conflict_clause = conflict
        dl = assignment.dl
        #first resolve the conflict clause with the conflicting assignment's clause
        logging.debug("Resolving: %s with %s",assignment.clause,conflict_clause)
        new_clause = assignment.clause.resolve(conflict_clause)
        logging.debug(" -> %s",new_clause)
        l = new_clause.max_lit
        while True:
            logging.debug("Resolving: %s with %s",new_clause,l.variable.stk_ptr.clause)
            new_clause = new_clause.resolve(l.variable.stk_ptr.clause)
            logging.debug(" -> %s",new_clause)
            if len(new_clause)==0:
                logging.info("Resolved the empty clause")
                return -1
            elif len(new_clause)==1:
                #single literal clause
                logging.debug("Resolved a single literal clause: %s",new_clause)
                self.clauses.append(new_clause)
                solo = new_clause.literals[0]
                logging.info("Learned: %s -> %s = %s",new_clause,solo.variable,solo.polarity)
                return 0
            #if new_clause == UIP, add it to occurrence lists and return new dl
            refA = new_clause.literals[new_clause.refA]
            refB = new_clause.literals[new_clause.refB]
            if refB.variable.stk_ptr.dl != refA.variable.stk_ptr.dl:
                logging.debug("UIP Because: %s",refA)
                logging.info("Adding clause: %s",new_clause)
                new_clause.link()
                self.clauses.append(new_clause)
                #return the second highest decision level
                return refB.variable.stk_ptr.dl
            l = new_clause.max_lit
    def BackTrack(self):
        #clean up every assignment >= self.dl
        # remove from stack and unassign
        logging.info("Returning to decision level: %s",self.dl)
        while len(self.stack) and self.stack[-1].dl >= self.dl +1:
            a = self.stack.pop()
            logging.debug("Unassigning: %s",a.var)
            a.var.unassign()
            a.var.waiting = False
    def assign(self,x,v):
        #branching assignments do not have an asserting clause (None)
        a = Assignment(self.dl,x,v,None)
        self.stack.push(a)
        x.assign(a)
    def CDCL(self):
        if self.pre_condition_CONFLICT:
            return "UNSAT"
        self.dl = 0
        while not self.AllVariablesAssigned():
            x,v = self.PickBranchingVariable()
            self.dl += 1
            self.assign(x,v)
            r = self.UnitPropagation()
            if r:
                b = self.ConflictAnalysis(r)
                logging.debug("ConflictAnalysis returned: %s",b)
                if b<0:
                    return "UNSAT"
                else:
                    self.dl = b-1
                    self.BackTrack()
                if b==0:
                    logging.info("RESTART")
                    self.setup()
                    return self.CDCL()
        return "SAT"
