call "%VS71COMNTOOLS%vsvars32.bat"
REM Python24 gives an "invalid group reference" error
C:\Python23\python ..\updateVersion.py
C:\Python24\python make_py_dist.py
C:\Progra~1\nsis\makensis eclass-builder.nsi
REM C:\Python24\python make_py_dist.py --unicode
REM C:\Progra~1\nsis\makensis eclass-builder.nsi