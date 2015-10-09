# pyalazar

Native Python api for Alazar Technologies GS/s digitizer modules.

This package currently supports the ATS-9870 and the ATS-9360.

##Package design

The core of the package is board.pyx, defining the Python api which will be compiled by Cython.

The actual Cython wrapping of the C API is specified in c_alazar_api.pxd

Data processing modules which interpret the raw digitizer data are defined in processor.py

To enable data processing to keep up with the very high data acquisition rates achieved by these digitizers, the tasks of draining the digitizer memory buffers and actually processing the data are handled in two separate processes using the multiprocessing module.  Board buffers are emptied into a processing queue which is drained by the data processing process, passing each buffer to the set of data processing objects.  At the end of the acquisition, these processors are passed back to the main process and returned to the caller.

##Tests

The data processor objects are reasonably well tested.  Run tests using nose from the root package directory.

Without a physical mock, testing the board API is mostly meaningless.

##Compiling on Windows

Compiling Cython code on windows is slightly tricky (and immensely frustrating).

First, install Anaconda.  This includes Cython.

There's a page on the Cython wiki about the windows compiler issue that we will now work around:
https://github.com/cython/cython/wiki/CythonExtensionsOnWindows

From that page (following the permanent workaround from the first method):

1. Install Microsoft Visual C++ Compiler for Python from http://www.microsoft.com/en-us/download/details.aspx?id=44266

2. Patch the file `C:\yourpythoninstall\Lib\distutils\msvc9compiler.py` (here yourpythoninstall will be anaconda) by adding the following code at the top of the find_vcvarsall() function:

        def find_vcvarsall(version):
            """Find the vcvarsall.bat file

            At first it tries to find the productdir of VS 2008 in the registry. If
            that fails it falls back to the VS90COMNTOOLS env var.
            """
            vsbase = VS_BASE % version
            vcpath = os.environ['ProgramFiles']
            vcpath = os.path.join(vcpath, 'Common Files', 'Microsoft',
                'Visual C++ for Python', '9.0', 'vcvarsall.bat')
            if os.path.isfile(vcpath): return vcpath
            vcpath = os.path.join(os.environ['LOCALAPPDATA'], 'Programs', 'Common', 'Microsoft', 'Visual C++ for Python', '9.0', 'vcvarsall.bat')
            if os.path.isfile(vcpath): return vcpath
            ...

3. Create a file distutils.cfg in the same folder (for anaconda this should already exist), and put this inside:

        [build]
        compiler=msvc

Now you can compile C extensions without any prior manipulations.

There were a couple of very particular details in setup.py that turn out to be crucial for compilation to work on Windows when it needs to link to external libraries.

Specifically, when we define the Extension that we pass to cythonize(),

    hello = Extension('alazar_hello_world',
                      sources = ['alazar_hello_world.pyx'],
                      include_dirs = ['C:\\AlazarTech\\ATS-SDK\\6.2.0\\Samples\\Include'],
                      libraries = ['ATSApi'],
                      library_dirs = ['C:\\AlazarTech\\ATS-SDK\\6.2.0\\Samples\\Library\\x64'],)

the library name (the first parameter passed to Extension) MUST be the same as the .pyx file or something goes horribly wrong with linking.

To compile, from the directory ```alazar/``` run the command

```python.exe setup.py build_ext --inplace --compiler=msvc```