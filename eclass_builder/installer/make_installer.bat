call "%VS90COMNTOOLS%vsvars32.bat"
C:\Python25\python ..\updateVersion.py %1
nmake -f makefile.vc
cd ..\autorun\loader
nmake -f loader.mak
cd ..\..
C:\Python25\python runTests.py
cd installer
C:\Python25\python make-installer.py
C:\Progra~1\nsis\makensis eclass-builder.nsi
