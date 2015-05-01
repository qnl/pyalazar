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

