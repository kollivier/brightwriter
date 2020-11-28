from __future__ import print_function
from builtins import str
import os, sys

rootdir = os.path.abspath(sys.path[0])
if not os.path.isdir(rootdir):
    rootdir = os.path.dirname(rootdir)
figfile = os.path.join(rootdir, 'tests.figleaf')

if os.path.exists(figfile):
    os.remove(figfile)

hasFigleaf=False
try:
    import figleaf
    figleaf.start()
    hasFigleaf=True
except:
    pass

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
#import index
import converter
import library.metadata

alltests = unittest.TestSuite(( encrypt.getTestSuite(), 
                                analyzer.getTestSuite(),
                                #index.getTestSuite(),
                                converter.getTestSuite(),
                                library.metadata.getTestSuite(),
                              ))

results = unittest.TestResult()
alltests.run(results)

if results.wasSuccessful():
    print("%d tests passed!" % (results.testsRun))
else:
    print("\n%d tests failed!\n" % (len(results.failures)))
    for error in results.failures:
        print("------ " + str(error[0]) + " ------")
        print(error[1])
        
    for error in results.errors:
        print("------ " + str(error[0]) + " ------")
        print(error[1])
    sys.exit(1)

if hasFigleaf:
    figleaf.stop()
    figleaf.write_coverage(figfile)

    # generate a spiffy HTML report from this
    os.system("figleaf2html -d ./tests_code_coverage %s" % figfile)
