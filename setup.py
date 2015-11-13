# Copyright (C) 2015  Chris Macklin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Cython-based support of Alazar digitizers."""
import os.path
from setuptools import setup, Extension
import numpy

USE_CYTHON = True
try:
    from Cython.Build import cythonize
except ImportError:
    USE_CYTHON = False

doclines = __doc__.split('\n')

ext = '.pyx' if USE_CYTHON else '.c'

ext_path = os.path.join("alazar", "board" + ext)

alazar_SDK_path = "C:\\AlazarTech\\ATS-SDK\\6.2.0\\"

python_is_64bit = True

if python_is_64bit:
    library_path = 'Samples\\Library\\x64'
else:
    library_path = 'Samples\\Library\\Win32'

extensions = [Extension('board',
                       sources = [ext_path,],
                       include_dirs = [alazar_SDK_path + 'Samples\\Include',],
                       libraries = ['ATSApi',],
                       library_dirs = [alazar_SDK_path + library_path, ],)]

if USE_CYTHON:
    extensions = cythonize(extensions)

setup(name='pyalazar',
      version='0.1',
      description = doclines[0],
      long_description = '\n'.join(doclines[2:]),
      url='http://github.com/qnl/pyalazar',
      author='Chris Macklin',
      author_email='chris.macklin@berkeley.edu',
      license='GPL2',
      packages=['alazar'],
      install_requires=['numpy'],
      ext_modules=extensions,
      include_dirs=[numpy.get_include()],
      )