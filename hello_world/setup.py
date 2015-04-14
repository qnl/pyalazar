from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension

config = {
    'description': 'Python interface for Alazar digitzer',
    'author': 'Chris Macklin',
    'url': '',
    'download_url': '',
    'author_email': 'chris.macklin@berkeley.edu',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['alazar'],
    'scripts': [],
    'name': 'pyalazar'
}

# setup(ext_modules = cythonize(['alazar_hello_world.pyx']))

hello = Extension('alazar_hello_world',
                  sources = ['alazar_hello_world.pyx'],
                  include_dirs = ['C:\\AlazarTech\\ATS-SDK\\6.2.0\\Samples\\Include'],
                  libraries = ['ATSApi'],
                  library_dirs = ['C:\\AlazarTech\\ATS-SDK\\6.2.0\\Samples\\Library\\x64','C:\\AlazarTech\\ATS-SDK\\6.2.0\\Samples_CSharp\\'],)

setup(ext_modules = cythonize([hello]),
      **config
)

