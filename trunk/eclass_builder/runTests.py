import sys
import unittest
import encrypt
import analyzer

alltests = unittest.TestSuite(( encrypt.getTestSuite(), 
                                analyzer.getTestSuite(),  
                              ))

results = unittest.TestResult()
alltests.run(results)

if results.wasSuccessful():
    print "%d tests passed!" % (results.testsRun)
    sys.exit(0)
else:
    print "\n%d tests failed!\n" % (len(results.failures))
    for error in results.failures:
        print "------ " + str(error[0]) + " ------"
        print error[1]
        
    for error in results.errors:
        print "------ " + str(error[0]) + " ------"
        print error[1]
    sys.exit(1)
        