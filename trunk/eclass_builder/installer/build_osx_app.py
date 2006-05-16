from distutils.core import setup
import py2app
import glob
import version

myplist = dict(
    CFBundleIdentifier='net.eclass.eclass_builder',
    CFBundleDisplayName="EClass.Builder",
    CFBundleVersion=version.asString()
    )
 
rootdir = "../"

py2app_options = dict(
	iconfile=rootdir + "icons/eclass_builder.icns", 
    argv_emulation=True,
    plist=myplist
)

setup(
    name="EClass.Builder",
    app=[rootdir + 'eclass_builder.py'],
    data_files=[('', 	glob.glob(rootdir + '3rdparty') + 
    						glob.glob(rootdir + 'about') +
    						glob.glob(rootdir + 'autorun') +
    						glob.glob(rootdir + 'convert') +
    						glob.glob(rootdir + 'docs') +
    						glob.glob(rootdir + 'greenstone') +
    						glob.glob(rootdir + 'icons') +
    						glob.glob(rootdir + 'locale') +
    						glob.glob(rootdir + 'license') +
    						glob.glob(rootdir + 'plugins') +
    						glob.glob(rootdir + 'themes') +
    						[rootdir + "bookfile.book.in"]
    						)
    			],
    options=dict(py2app=py2app_options),
)
