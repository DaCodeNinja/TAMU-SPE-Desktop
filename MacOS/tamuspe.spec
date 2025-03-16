a = Analysis(
    ['tamu-spe.py'],
    pathex=[],
    binaries=[],
    datas=[('src/settings.yaml', 'src'), ('src/feedback.ui', 'src'), ('src/info_widget.ui', 'src'), ('src/settings.ui', 'src')],
    hiddenimports=['yaml', 'pync'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# For macOS, create an application bundle
app = BUNDLE(exe,
             name='TAMU-SPE.app',
             icon="images/SPE_A_M_RGB_square.icns",
             bundle_identifier='com.albertoalvarez.tamuspe',
             version='1.0.0',
             info_plist={
                 'NSHighResolutionCapable': 'True',
                 'LSBackgroundOnly': 'False',
                 'LSUIElement': 'NO',  # Set to 'YES' to hide from Dock
                 'CFBundleDisplayName': 'TAMU-SPE',
                 'CFBundleVersion': '1.0',
                 'CFBundleShortVersionString': '1.0.0',
             }
)


#coll = COLLECT(
#    exe,
#    a.binaries,
#    a.datas,
#    strip=False,
#    upx=True,
#    upx_exclude=[],
#    name='tamu-spe',
#)