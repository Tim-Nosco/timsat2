from util import Assignment, AssignmentStack, Variable, Literal, Clause
import logging

class Solver:
    def __init__(self,parser):
        self.vars = [parser.known[x] for x in parser.known]
        self.vars.sort(key=lambda x: x.count)
        self.current_var = 0
        self.dl = 0
        #create assignment stack
        self.stack = AssignmentStack()
        for clause in parser.clauses:
            #check for single variable or empty clauses (unsat or unit)
            s = clause.status()
            if s == "UNSAT":
                #empty clause
                logging.warning("Found empty clause")
                self.pre_condition_CONFLICT = True
                break
            elif s == "UNIT":
                #single literal clause
                logging.debug("Single literal clause: {}".format(clause))
                #add assignment to stack
                literal = clause.literals[0]
                a = Assignment(0,literal.variable,literal.polarity,clause)
                logging.debug(" Learned: {} -> {}".format(literal.variable,literal.polarity))
                self.stack.push(a)
                if self.UnitPropagation():
                    self.pre_condition_CONFLICT = True
                    break
            else:
                #setup occurrence lists
                for literal in clause:
                    literal.occurrence_link(clause)
    def Model(self):
        return dict((v.name,v.value()) for v in self.vars)
    def nextvar(self):
        r = self.vars[self.current_var]
        self.current_var += 1
        return r
    def PickBranchingVariable(self):
        r = self.nextvar()
        while r.isAssigned():
            r = self.nextvar(0)
        logging.info("Branching: {} -> {}".format(r.name,False))
        return r,False
    def AllVariablesAssigned(self):
        return all(x.isAssigned() for x in self.vars)
    def UnitPropagation(self):
        if len(self.stack)<0:
            return False
        current = len(self.stack)-1
        while current_ptr < len(self.stack):
            a = self.stack[current]
            a.var.assign(a)
            for clause in a.var.occurrance[a.val]:
                case = clause.status()
                logging.debug("Clause: {}\n Class {}".format(clause,case))
                if case=="UNSAT":
                    logging.info("Conflict on clause: {}".format(clause))
                    return True
                elif case=="UNIT":
                    l = clause.unitLiteral
                    new_assignment = Assignment(self.dl,l.variable,l.polarity,clause)
                    self.stack.push(new_assignment)
                    logging.info("Learned: {} -> {}".format(l.variable.name,l.polarity))
            current += 1

    def ConflictAnalysis(self):
        pass
    def BackTrack(self):
        pass
    def CDCL(self):
        if self.pre_condition_CONFLICT:
            return "UNSAT"
        self.dl = 0
        while not self.AllVariablesAssigned():
            x,v = self.PickBranchingVariable()
            self.dl += 1
            self.assign(x,v)
            if self.UnitPropagation():
                b = self.ConflictAnalysis()
                if b<0:
                    return "UNSAT"
                else:
                    self.BackTrack()
                    self.dl = b
        return "SAT"
