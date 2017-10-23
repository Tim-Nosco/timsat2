from interpret import Parser
from util import Assignment, AssignmentStack, Variable, Literal, Clause
from solver import Solver
import unittest

class TestStack(unittest.TestCase):
    def test_assignment(self):
        v = Variable("1")
        s = AssignmentStack()
        a = Assignment(1,v,True,Clause(Literal(v)))
        s.push(a)
        p = s.pop()
        self.assertEqual(p.var, v)        

class TestVariable(unittest.TestCase):
    def setUp(self):
        self.v = Variable("1")
        self.a = Assignment(1,self.v,True,Clause(Literal(self.v)))
    def test_repr(self):
        v = Variable("somename")
        self.assertEqual(str(v),"somename")
    def test_value(self):
        #v starts unassigned
        self.assertEqual(self.v.value(),None)
        #associate v
        self.v.assign(self.a)
        #v should be assigned true
        self.assertTrue(self.v.value())
        #disassociate v
        self.v.unassign()
        #v should be unassigned
        self.assertFalse(self.v.isAssigned())

class TestLiteral(unittest.TestCase):
    def setUp(self):
        self.v1 = Variable("1")
        self.v2 = Variable("2")
        self.l1 = Literal(self.v1)
        self.l2 = Literal(self.v2)
        self.l3 = Literal(self.v1,False)
        self.a = Assignment(1,self.v2,True,Clause(self.l2))
        self.v2.assign(self.a)
    def test_eq(self):
        t = Literal(self.v1)
        self.assertEqual(t,self.l1)
        self.assertNotEqual(self.l1,self.l3)
        self.assertNotEqual(self.l1,self.l2)
    def test_neg(self):
        self.assertEqual(self.l3,-self.l1)
    def test_value(self):
        self.assertTrue(self.l2.value())

class TestClause(unittest.TestCase):
    def setUp(self):
        self.v1 = Variable("1")
        self.v2 = Variable("2")
        self.v3 = Variable("3")
        self.l1 = Literal(self.v1)
        self.l2 = Literal(self.v2)
        self.l3 = Literal(self.v2,False)
        self.a1 = Assignment(1,self.v2,True,Clause(self.l2))
        self.v2.assign(self.a1)
    def test_init(self):
        c = Clause()
        self.assertFalse(hasattr(c,'revA') or hasattr(c,'revB'))
        c = Clause(Literal(self.v1,True))
        self.assertFalse(hasattr(c,'revA') or hasattr(c,'revB'))
    def test_eq(self):
        c1 = Clause(self.l1)
        c2 = Clause(self.l2)
        c3 = Clause(self.l1)
        self.assertEqual(c1,c3)
        self.assertNotEqual(c1,c2)
    def test_contains(self):
        c1 = Clause(self.l1)
        c2 = Clause(self.l2)
        self.assertTrue(self.l1 in c1)
        self.assertFalse(self.l1 in c2)
    def test_status(self):
        #empty clause
        c = Clause()
        self.assertEqual(c.status(),"UNSAT")
        #single literal
        # unassigned
        c = Clause(self.l1)
        self.assertEqual(c.status(),"UNIT")
        # sat
        c = Clause(self.l2)
        self.assertEqual(c.status(),"SAT")
        # unsat
        c = Clause(self.l3)
        self.assertEqual(c.status(),"UNSAT")
        #two-literal
        # unit
        c = Clause(self.l1, self.l3)
        self.assertEqual(c.status(),"UNIT")
        # sat
        c = Clause(self.l2, self.l3)
        self.assertEqual(c.status(),"SAT")
        c = Clause(self.l1, self.l2)
        self.assertEqual(c.status(),"SAT")
        # unsat
        c = Clause(self.l3, self.l3)
        self.assertEqual(c.status(),"UNSAT")
        #multi-literal
        # c = Clause(self.l3, self.l1, self.l3)
        # self.assertEqual(c.status(),"UNIT")
        c = Clause(self.l3, self.l1, self.l1)
        self.l3.occurrence_link(c)
        self.assertEqual(c.status(),"UNRESOLVED")
        c = Clause(self.l3,self.l1,self.l2)
        c.link()
        self.assertEqual(c.status(),"SAT")

    def test_resolution(self):
        c1 = Clause(self.l1,self.l2)
        c2 = Clause(self.l1,self.l3)
        c3 = c1.resolve(c2)
        self.assertEqual(c3,Clause(self.l1))


class TestParser(unittest.TestCase):
    def test_nocmnts(self):
        p = Parser(lines="1 3 -4 0")
        c = p.clauses
        k = p.known
        #there is only 1 clause
        self.assertEqual(len(c),1)
        c = c[0]
        #the clause has 3 literals
        self.assertEqual(len(c),3)
        #there are 3 variables
        self.assertEqual(len(k),3)
        #ensure each variable appers with correct polarity
        self.assertTrue(Literal(k['1']) in c)
        self.assertTrue(Literal(k['3']) in c)
        self.assertTrue(Literal(k['4'],False) in c)
    def test_cmnts(self):
        pass
    def test_header(self):
        pass

if __name__=="__main__":
    unittest.main()
