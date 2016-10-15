#!/usr/bin/env python

from cx_Freeze import setup, Executable
from os import getcwd, path
from shutil import rmtree
from sys import argv, platform


def SetupBuild():

    app = 'spytify'
    base = 'Win32GUI' if platform == 'win32' else None
    curpath = path.dirname(path.realpath(argv[0]))
    filpath = path.join(curpath, 'Others')
    apppath = path.join(curpath, app)

    build_options = {'include_files': [filpath + '/icon.ico']}
        
    if platform == 'linux':
        qtlibpath = '/opt/Qt/5.5/gcc_64/lib'
        gnupath = '/usr/lib/x86_64-linux-gnu'
        lapackpath='/usr/lib/liblapack.so.3'

        build_options['include_files'].extend([
            path.join(filpath, app + '.linux'),
            (path.join(qtlibpath, 'libQt5XcbQpa.so.5'), 'libQt5XcbQpa.so.5'),
            (path.join(qtlibpath, 'libQt5DBus.so.5'), 'libQt5DBus.so.5'),
            (path.join(gnupath, 'libSDL-1.2.so.0'), 'libSDL-1.2.so.0'),
            (path.join(gnupath, 'libSDL_mixer-1.2.so.0'), 'libSDL_mixer-1.2.so.0'),
            (path.join(gnupath, 'libSDL_image-1.2.so.0'), 'libSDL_image-1.2.so.0'),
            (path.join(gnupath, 'libSDL_ttf-2.0.so.0'), 'libSDL_ttf-2.0.so.0'),
            (path.join(gnupath, 'libmikmod.so.2'), 'libmikmod.so.2'),
            (lapackpath, lapackpath.rpartition('/')[2]),
        ])

    setup(
        name = app.capitalize(),
        version = '1.0',
        description = 'Music Streaming Service',
        options = {'build_exe': build_options},
        executables = [Executable(apppath + '.py', base = base, icon = filpath + '/icon.ico')])


SetupBuild()
