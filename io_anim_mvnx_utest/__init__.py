# -*- coding:utf-8 -*-


"""
General module for the unit testing of this repository.
It can be used to run specific tests within Python. Doc:
https://docs.python.org/3/library/unittest.html#assert-methods
"""


__author__ = "Andres FR"


from os.path import dirname, abspath
import unittest


UTEST_DIR = dirname(abspath(__file__))


def run_testmethod(moduleclassmethod, verbosity=2):
    """
    Given a string holding a fully qualified reference to a method of a
    unittest.Testcase (e.g. 'test.foo_test.FooTestCaseCpu.test_loop'), runs the
    method and returns the results as an instance of
    unittest.runner.TextTestResult.
    """
    # this returns the contents of the module as a unittest.TestSuite
    tests = unittest.TestLoader().loadTestsFromName(moduleclassmethod)
    # run and return results
    test_results = unittest.TextTestRunner(verbosity=verbosity).run(tests)
    return test_results


def run_testmethods(moduleclassmethods, verbosity=2):
    """
    Like run_testmethod, but receives a collection of strings and joins the
    methods into a single TestSuite before testing.
    """
    tests = unittest.TestLoader().loadTestsFromNames(moduleclassmethods)
    # run and return results
    test_results = unittest.TextTestRunner(verbosity=verbosity).run(tests)
    return test_results


def run_testcase(testcase, verbosity=2):
    """
    Given the reference to a subclass of unittest.Testcase, runs the unittests
    it contains and returns the results as an instance of
    unittest.runner.TextTestResult.
    """
    # this returns the contents of the module as a unittest.TestSuite
    tests = unittest.TestLoader().loadTestsFromTestCase(testcase)
    # run and return results
    test_results = unittest.TextTestRunner(verbosity=verbosity).run(tests)
    return test_results


def run_testcases(testcases, verbosity=2):
    """
    Like run_testcase, but receives a collection of classes and joins all their
    tests into a single TestSuite before testing.
    """
    tests = unittest.TestSuite()
    for c in testcases:
        tests.addTests(unittest.TestLoader().loadTestsFromTestCase(c))
    # run and return results
    test_results = unittest.TextTestRunner(verbosity=verbosity).run(tests)
    return test_results


def run_module(module, verbosity=2):
    """
    Given the reference to a module, runs the unittests it contains and returns
    the results as an instance of unittest.runner.TextTestResult.
    """
    # this returns the contents of the module as a unittest.TestSuite
    tests = unittest.TestLoader().loadTestsFromModule(module)
    # run and return results
    test_results = unittest.TextTestRunner(verbosity=verbosity).run(tests)
    return test_results


def run_modules(modules, verbosity=2):
    """
    Like run_module, but receives a collection of modules and joins all their
    tests into a single TestSuite before testing.
    """
    tests = unittest.TestSuite()
    for m in modules:
        tests.addTests(unittest.TestLoader().loadTestsFromModule(m))
    # run and return results
    test_results = unittest.TextTestRunner(verbosity=verbosity).run(tests)
    return test_results


def run_all_tests(test_rootdir=UTEST_DIR, verbosity=2):
    """
    This function is the equivalent to
    python3 -m unittest discover -s test_rootdir -t REPO_DIR -p "*_test.py" -v
    with the difference that it returns the test report as an instance of
    unittest.runner.TextTestResult.
    """
    suite = unittest.TestLoader().discover(test_rootdir, "*_test.py",
                                           test_rootdir)
    results = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return results


if __name__ == "__main__":
    run_all_tests()
