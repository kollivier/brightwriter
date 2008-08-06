call "%VS71COMNTOOLS%vsvars32.bat"
REM Python24 gives an "invalid group reference" error
C:\Python25\python ..\updateVersion.py %1
C:\Python25\python make_py_dist.py --unicode
C:\cx_Freeze-3.0.3\FreezePython --exclude-modules=wx --install-dir librarian-win32 ../librarian.py
nmake -f makefile.vc
cd ..\autorun\loader
nmake -f loader.mak
cd ..\..
C:\Python25\python runTests.py
cd installer
C:\Progra~1\nsis\makensis eclass-builder.nsi
REM C:\Python25\python make_py_dist.py --unicode
REM C:\Progra~1\nsis\makensis eclass-builder.nsi