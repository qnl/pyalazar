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
from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension
import numpy

config = {
    'description': 'Python interface for Alazar digitzer',
    'author': 'Chris Macklin',
    'url': '',
    'download_url': '',
    'author_email': 'chris.macklin@berkeley.edu',
    'version': '0.1',
    'install_requires': ['nose','numpy'],
    'packages': ['alazar'],
    'scripts': [],
    'name': 'pyalazar'
}

alazar_SDK_path = "C:\\AlazarTech\\ATS-SDK\\6.2.0\\"

# 32-bit:
# library_path = 'Samples\\Library\\Win32'
# 64-bit:
library_path = 'Samples\\Library\\x64'


alazar = Extension('board',
                  sources = ['board.pyx',],
                  include_dirs = [alazar_SDK_path + 'Samples\\Include',],
                  libraries = ['ATSApi',],
                  library_dirs = [alazar_SDK_path + library_path, ],)

setup(ext_modules = cythonize([alazar]),
      include_dirs=[numpy.get_include()],
      **config
)

