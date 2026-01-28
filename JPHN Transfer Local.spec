# -*- mode: python ; coding: utf-8 -*-
# JPHN Transfer Local Server - PyInstaller Spec File
# Build command: pyinstaller "JPHN Transfer Local.spec"

import os

block_cipher = None

# Get the current directory
SPEC_DIR = os.path.dirname(os.path.abspath(SPECPATH))

a = Analysis(
    ['run_local_exe.py'],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('db_config.py', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'sqlalchemy',
        'sqlalchemy.dialects.postgresql',
        'psycopg2',
        'psycopg2.extras',
        'psycopg2.extensions',
        'werkzeug',
        'werkzeug.security',
        'jinja2',
        'markupsafe',
        'itsdangerous',
        'click',
        'blinker',
        'email_validator',
        'wtforms',  # If used
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='JPHN Transfer Local',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console to see server logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: icon='icon.ico'
)
