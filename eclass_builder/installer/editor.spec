a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), '..\\editor.py'],
             pathex=['F:\\oss\\eclass\\eclass_builder\\installer'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name='buildeditor/editor.exe',
          debug=0,
          strip=0,
          upx=1,
          console=0 )
coll = COLLECT( exe,
               a.binaries,
               strip=0,
               upx=0,
               name='disteditor')
