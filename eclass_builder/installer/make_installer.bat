call "%VS90COMNTOOLS%vsvars32.bat"
C:\Python26\python ..\updateVersion.py %1
nmake -f makefile.vc
cd ..
C:\Python26\python runTests.py
cd installer
C:\Python26\python make-installer.py
cp C:\Python26\msvcr90.dll dist
cp C:\Python26\msvcm90.dll dist
cp C:\Python26\msvcp90.dll dist
cp C:\Python26\Microsoft.VC90.CRT.manifest dist
C:\Progra~2\nsis\makensis eclass-builder.nsi
