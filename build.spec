# PyInstaller spec — genera ControlParental.exe con elevación UAC automática
# Uso: pyinstaller build.spec --clean

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "anthropic",
        "anthropic._models",
        "anthropic.resources",
        "telegram",
        "telegram.ext",
        "telegram._bot",
        "telegram.ext._application",
        "keyboard",
        "asyncio",
        "threading",
        "tkinter",
        "tkinter.simpledialog",
        "tkinter.messagebox",
        "httpx",
        "httpcore",
        "anyio",
        "certifi",
        "logger",
        "monitor",
        "overlay",
        "telegram_bot",
        "ia_classifier",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytesseract", "PIL", "pyperclip", "pyautogui"],
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
    name="ControlParental",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # Sin ventana de consola
    uac_admin=True,      # Pide elevación UAC al ejecutar
    icon=None,
)
