a = Analysis(
    ['tamu-spe.py'],
    pathex=[],
    binaries=[],
    datas=[('src/settings.yaml', 'src'), ('src/feedback.ui', 'src'), ('src/info_widget.ui', 'src'), ('src/settings.ui', 'src')],
    hiddenimports=['yaml'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TAMUSPE_ONDEMAND',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True if your application has a GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# For macOS, create an application bundle
app = BUNDLE(exe,
             name='TAMU-SPE OnDemand.app',
             icon="images/SPE_A_M_RGB_square.icns",
             bundle_identifier='com.albertoalvarez.tamuspe',
             version='1.0.0',
             info_plist={
                 'NSHighResolutionCapable': 'True',
                 'LSBackgroundOnly': 'False',
                 'LSUIElement': 'NO',  # Set to 'YES' to hide from Dock
                 'CFBundleDisplayName': 'TAMU-SPE OnDemand',
                 'CFBundleVersion': '1.0',
                 'CFBundleShortVersionString': '1.0.0',
             }
)