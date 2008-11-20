call "%VS90COMNTOOLS%vsvars32.bat"
C:\Python26\python ..\updateVersion.py %1
C:\Python26\python make_py_dist.py --unicode
nmake -f makefile.vc
cd ..\autorun\loader
nmake -f loader.mak
cd ..\..
C:\Python26\python runTests.py
cd installer
C:\Progra~1\nsis\makensis eclass-builder.nsi
