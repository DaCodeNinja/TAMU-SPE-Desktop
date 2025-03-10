# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../etc/settings.yaml', 'etc'),
        ('../etc/feedback.ui', 'etc'),
        ('../etc/info_widget.ui', 'etc'),
        ('../etc/settings.ui', 'etc'),
        ('../etc/splashscreen.ui', 'etc'),
        ('../etc/TAMUSPE_Square.ico', 'etc'),
        ('../etc/.env', 'etc'),
        ('../media/loading.gif', 'media'),
        ('../pyarrow', 'pyarrow')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TAMU-SPE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if your application has a GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,  # Set to True to create a single executable file
    icon='../images/spe_rgb_square_icon.ico',  # Specify the path to your icon file
)


coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, [], name='TAMU-SPE')
