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
                logging.info("pre_condition: Found UNSAT clause: {}".format(clause))
                self.pre_condition_CONFLICT = True
                break
            elif s == "UNIT":
                #single literal clause
                logging.debug("pre_condition: Single literal clause: {}".format(clause))
                #add assignment to stack
                literal = clause.literals[0]
                a = Assignment(0,literal.variable,literal.polarity,clause)
                logging.info("Learned: {} -> {} = {}".format(clause,literal.variable,literal.polarity))
                self.stack.push(a)
                if self.UnitPropagation():
                    self.pre_condition_CONFLICT = True
                    break
    def Model(self):
        return dict((v.name,v.value()) for v in self.vars)
    def nextvar(self):
        for v in self.vars:
            if not v.isAssigned():
                return v
    def PickBranchingVariable(self):
        r = self.nextvar()
        while r.isAssigned():
            r = self.nextvar(0)
        logging.info("Branching dl: {} -> {} = {}".format(self.dl+1,r.name,False))
        return r,False
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
                logging.debug("Clause: {}\n Case: {}".format(clause,case))
                if case=="UNSAT":
                    logging.info("Conflict on clause: {}".format(clause))
                    return a,clause
                elif case=="UNIT":
                    l = clause.unitLiteral
                    if not l.variable.waiting:
                        new_assignment = Assignment(self.dl,l.variable,l.polarity,clause)
                        self.stack.push(new_assignment)
                        l.variable.waiting = new_assignment
                        logging.info("Learned: {} -> {} = {}".format(clause,l.variable.name,l.polarity))
                    else:
                        #the variable hasn't been assigned yet because it was determined from a
                        # unit clause in this same loop
                        # there could be a conflict, so we must check before continuing
                        l.variable.assign(l.variable.waiting)
                        case = clause.status()
                        if case=="UNSAT":
                            logging.info("Conflict on clause: {}".format(clause))
                            return l.variable.waiting,clause
                        else:
                            l.variable.unassign()
            current += 1

    def ConflictAnalysis(self,conflict):
        assignment,conflict_clause = conflict
        dl = assignment.dl
        #first resolve the conflict clause with the conflicting assignment's clause
        new_clause = assignment.clause.resolve(conflict_clause)
        l = new_clause.max_lit
        while True:
            new_clause = new_clause.resolve(l.variable.stk_ptr.clause)
            if len(new_clause)==0:
                logging.info("Resolved the empty clause")
                return -1
            elif len(new_clause)==1:
                #single literal clause
                logging.debug("Resolved a single literal clause: {}".format(new_clause))
                self.clauses.append(new_clause)
                solo = new_clause.literals[0]
                logging.info("Learned: {} -> {} = {}".format(new_clause,solo.variable,solo.polarity))
                return 0
            at_dl = filter(lambda x: x.variable.stk_ptr.dl==l.variable.stk_ptr.dl,new_clause)
            #if new_clause == UIP, add it to occurrence lists and return new dl
            if len(at_dl) == 1:
                logging.debug("UIP Because: {}".format(at_dl[0]))
                logging.info("Adding clause: {}".format(new_clause))
                new_clause.link()
                self.clauses.append(new_clause)
                #return the second highest decision level
                return new_clause.literals[new_clause.refB].variable.stk_ptr.dl
            l = new_clause.max_lit
    def BackTrack(self):
        #clean up every assignment >= self.dl
        # remove from stack and unassign
        logging.info("Returning to decision level: {}".format(self.dl))
        while len(self.stack) and self.stack[-1].dl >= self.dl:
            a = self.stack.pop()
            logging.debug("Unassigning: {}".format(a.var))
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
                logging.debug("ConflictAnalysis returned: {}".format(b))
                if b<0:
                    return "UNSAT"
                else:
                    self.dl = b
                    self.BackTrack()
                    self.dl -=1
                if b==0:
                    logging.info("RESTART")
                    self.setup()
                    return self.CDCL()
        return "SAT"
