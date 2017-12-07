import unittest
from . import *

def info(func, input):
    return "%s(%s)" % (func, input)

class TestGocode(unittest.TestCase):
    
    def test_is_named(self):
        def false(input):
            self.assertFalse(is_named(input), info("is_named", input)) 
        def true(input):
            self.assertTrue(is_named(input), info("is_named", input)) 
            
        false("error")
        false("a")
        false("chan int")
        false("func(a, b int) error")
        true("a int")
        true("err error")
        true("c chan int")
        true("f func(a, b int) error")
    
    def test_parse_param_parts(self):
        def test(input, exp):
            res = parse_param_parts(input)
            self.assertEqual(res, exp, info("parse_param_parts", input))
            
        test("error", ["error"])        
        test("(int, error)", ["int", "error"])
        test("(a, b int, err error)", ["a", "b int", "err error"])
        test("(a int, f func(c, d int) error, err error)", ["a int", "f func(c, d int) error", "err error"])
        
    def test_parse_params(self):
        def test(input, exp):
            res = parse_params(input)
            self.assertEqual(res, exp, info("parse_params", input))

        test("error", [
            (None, "error")
        ])
        test("(int, error)", [
            (None, "int"), 
            (None, "error")
        ])
        test("(a, b int, err error)", [
            ("a", "int"),
            ("b", "int"),
            ("err", "error")
        ])
        test("(a int, f func(c, d int) error, err error)", [
            ("a", "int"),
            ("f", "func(c, d int) error"),
            ("err", "error")
        ])
        test("(a, b func(c, d int) error)", [
            ("a", "func(c, d int) error"),
            ("b", "func(c, d int) error")
        ])
        test("(a int, b []chan int)", [
            ("a", "int"),
            ("b", "[]chan int")
        ])
        test("(int, chan int)", [
            (None, "int"),
            (None, "chan int")
        ])
        
    def test_parse_func(self):
        def test(input, exp):
            res = parse_func(input)
            self.assertEqual(res, exp, info("parse_func", input))
        
        test("func(a int) error", (
            [("a", "int")], 
            [(None, "error")]
        ))
        test("func(a, b int, c chan int, d func(e error) error) (int, error)", (
            [
                ("a", "int"),
                ("b", "int"),
                ("c", "chan int"),
                ("d", "func(e error) error")
            ], [
                (None, "int"),
                (None, "error")
            ]
        ))
        test("func(a int) (num int, den int)", (
            [
                ("a", "int")
            ], [
                ("num", "int"),
                ("den", "int")
            ]
        ))
        
if __name__ == '__main__':
    unittest.main()
