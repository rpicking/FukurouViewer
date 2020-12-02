# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

additional_datas = [
    ('FukurouViewer/icon.ico', '.'),
    ('FukurouViewer/icon.png', '.'),
    ('FukurouViewer/migrate_repo', 'migrate_repo'),
    ('FukurouViewer/qml', 'qml'),
    ('FukurouViewer/audio', 'audio'),
    ('FukurouViewer/bin', 'bin'),
]

a = Analysis(['main.py'],
             pathex=['.', 'venv/Lib/site-packages'],
             binaries=[],
             datas=additional_datas,
             hiddenimports=[],
             hookspath=['hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='main')
