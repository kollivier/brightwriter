call "%VS90COMNTOOLS%vsvars32.bat"
C:\Python26\python ..\updateVersion.py %1
nmake -f makefile.vc
cd ..\autorun\loader
nmake -f loader.mak
cd ..\..
C:\Python26\python runTests.py
cd installer
C:\Python26\python make-installer.py
cp C:\Python26\msvcr90.dll
cp C:\Python26\Microsoft.VC90.CRT.manifest
C:\Progra~1\nsis\makensis eclass-builder.nsi
