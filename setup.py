# -*- coding: utf-8 -*-
import sys
import io
import setuptools
import tatsu

NAME = tatsu.__toolname__
PACKAGE = tatsu.__toolname__.lower()

SHORT_DESCRIPTION = (
    '{toolname} takes a grammar'
    ' in a variation of EBNF as input, and outputs a memoizing'
    ' PEG/Packrat parser in Python.'
).format(toolname=NAME)


try:
    from Cython.Build import cythonize
except ImportError:
    CYTHON = False
else:
    CYTHON = 'bdist_wheel' not in sys.argv

setuptools.setup(
    zip_safe=False,
    name='TatSu',
    version=tatsu.__version__,
    url='https://github.com/neogeny/{package}'.format(
        package=PACKAGE
    ),
    # download_url='https://bitbucket.org/neogeny/{package}/get/master.zip'.format(
    #     package=PACKAGE
    # ),
    author='Juancarlo Añez',
    author_email='apalala@gmail.com',
    maintainer='Juancarlo Añez',
    maintainer_email='apalala@gmail.com',
    description=SHORT_DESCRIPTION,
    long_description=io.open('README.rst', encoding='utf-8').read(),
    license='BSD License',
    packages=setuptools.find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'tatsu = tatsu:main',
            'g2e = tatsu.g2e:main',
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Cython',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Text Processing :: General'
    ],
    install_requires=[],
    setup_requires=['pytest-runner'],
    tests_require=['pytest-mypy'],
    extras_require={
        'future-regex': ['regex']
    },
    ext_modules=cythonize(
        "tatsu/**/*.py",
        exclude=[
            'tatsu/__main__.py',
            'tatsu/__init__.py',
            'tatsu/codegen/__init__.py',
            'tatsu/test/__main__.py',
            'tatsu/test/*.py'
        ]
    ) if CYTHON else [],
)
