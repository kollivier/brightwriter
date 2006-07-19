import sys
import unittest
import encrypt

alltests = unittest.TestSuite((encrypt.getTestSuite()))

results = unittest.TestResult()
alltests.run(results)

if results.wasSuccessful():
    print "All tests passed!"
    sys.exit(0)
else:
    print "\n%d tests failed!\n" % (len(results.failures))
    for error in results.failures:
        print "------ " + str(error[0]) + " ------"
        print error[1]
    sys.exit(1)
        