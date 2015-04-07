try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

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

setup(**config)