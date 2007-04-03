call "%VS71COMNTOOLS%vsvars32.bat"
REM Python24 gives an "invalid group reference" error
C:\Python24\python ..\updateVersion.py %1
C:\Python24\python make_py_dist.py --unicode
C:\cx_Freeze-3.0.1\FreezePython --exclude-modules=wx --install-dir librarian-win32 ../librarian.py
nmake -f makefile.vc
cd ..\autorun\loader
nmake -f loader.mak
cd ..\..\3rdparty\win32
unzip -o win32extras.zip
cd ..\..\installer
C:\Progra~1\nsis\makensis eclass-builder.nsi
REM C:\Python24\python make_py_dist.py --unicode
REM C:\Progra~1\nsis\makensis eclass-builder.nsi