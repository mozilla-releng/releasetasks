# -*- coding: utf-8 -*-
import unittest


from releasetasks import make_task_graph

class TestMakeTaskGraph(unittest.TestCase):
    def testSimpleGraph(self):
        expected = {
        }
        generated = make_task_graph(
            
        )
        self.assertEquals(expected, generated)
