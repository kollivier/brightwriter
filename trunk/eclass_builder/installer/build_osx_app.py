from distutils.core import setup
import py2app
import glob

myplist = dict(
    CFBundleIdentifier='net.eclass.eclass_builder',
    CFBundleDisplayName="EClass.Builder",
    CFBundleVersion="2.5.5.9"
    )
    
py2app_options = dict(
	iconfile="../icons/eclass_builder.icns", 
    argv_emulation=True,
    plist=myplist
)

setup(
    app=['../eclass_builder.py'],
    data_files=[('', 	glob.glob('../3rdparty') + 
    						glob.glob('../about') +
    						glob.glob('../autorun') +
    						glob.glob('../convert') +
    						glob.glob('../docs') +
    						glob.glob('../greenstone') +
    						glob.glob('../icons') +
    						glob.glob('../locale') +
    						glob.glob('../license') +
    						glob.glob('../plugins') +
    						['../swishe.conf'] +
    						glob.glob('../themes')
    						)
    			],
    options=dict(py2app=py2app_options),
)
