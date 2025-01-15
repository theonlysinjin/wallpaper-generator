from setuptools import setup

APP = ['change-wallpaper-macos.py']
DATA_FILES = [('Resources', ['resources/icon.icns'])]
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'LSUIElement': True,
        'CFBundleName': 'AI Wallpaper',
        'CFBundleDisplayName': 'AI Wallpaper',
        'CFBundleIdentifier': 'com.theonlysinjin.wallpaper-generator',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'CFBundleIconFile': 'icon.icns',
    },
    'packages': ['tkinter'],
}

setup(
    app=APP,
    name='AI Wallpaper',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
