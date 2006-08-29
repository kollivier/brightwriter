import os, sys

rootdir = os.path.abspath(sys.path[0])
if not os.path.isdir(rootdir):
    rootdir = os.path.dirname(rootdir)

# do this first because other modules may rely on _()
localedir = os.path.join(rootdir, 'locale')
import gettext
gettext.install('library', localedir)
lang_dict = {
			"en": gettext.translation('library', localedir, languages=['en']), 
			"es": gettext.translation('library', localedir, languages=['es']),
			"fr": gettext.translation('library', localedir, languages=['fr'])
			}
			

import unittest
import encrypt
import analyzer
import index
import library.metadata

alltests = unittest.TestSuite(( encrypt.getTestSuite(), 
                                analyzer.getTestSuite(),
                                index.getTestSuite(),
                                library.metadata.getTestSuite(),
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
        