# -*- coding: utf-8 -*-

__version__ = "$Id: setup.py 223 2013-09-26 11:57:35Z campr $"

from distutils.core import setup
import zipfile
import py2exe
import os
import update_version_info
import shutil
import PySide

# automatically extract path to PySide
dir_pyside = os.path.dirname(PySide.__file__)
data_file_phonon = os.path.join(dir_pyside, 'plugins', 'phonon_backend', 'phonon_ds94.dll')

if not os.path.exists:
    raise Exception('Cannot find data file for phonon: %s' % (data_file_phonon))

# setup for py2exe
setup(name="Tovian",
      version="1.0",
      author="Pavel Campr, Milan Herbig",
      author_email="campr@kky.zcu.cz, herbig@students.zcu.cz",
      data_files=[('phonon_backend', [data_file_phonon])],

      # py2exe setup:
      windows=[{
           "script": '../../tovian_gui.py'
      }],
      console=[{
           "script": '../../tovian_cli.py'
      }],
      options={"py2exe": {
          "bundle_files": 3, # 2 and 1 fails
          "includes": ["tovian", "PySide", "MySQLdb", "yaml"],
          "packages": ["sqlalchemy.dialects.mysql", "sqlalchemy.dialects.sqlite", "MySQLdb"],
          "excludes": ["nose", "unittest"]
      }}
)

# copy data files
if os.path.isdir('dist/data'):
    shutil.rmtree('dist/data')

shutil.copytree('../../data', 'dist/data')

shutil.copy('../../config.ini.dist', 'dist')
shutil.copy('additional_files/update.bat', 'dist')

# create zip file
target_dir = 'dist'
revision = update_version_info.get_revision('../..')
zip = zipfile.ZipFile('tovian_win32_%s.zip' % (revision), 'w', zipfile.ZIP_DEFLATED)
rootlen = len(target_dir) + 1
for base, dirs, files in os.walk(target_dir):
   for file in files:
      fn = os.path.join(base, file)
      zip.write(fn, fn[rootlen:])
