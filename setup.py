# -*- coding: utf-8 -*-
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

LONG_DESCRIPTION = io.open('README.rst', encoding='utf-8').read()


setuptools.setup(
    zip_safe=False,
    name='TatSu',
    version=tatsu.__version__,
    url='https://github.com/neogeny/{package}'.format(
        package=PACKAGE
    ),
    author='Juancarlo Añez',
    author_email='apalala@gmail.com',
    maintainer='Juancarlo Añez',
    maintainer_email='apalala@gmail.com',
    description=SHORT_DESCRIPTION,
    long_description=LONG_DESCRIPTION,
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
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Text Processing :: General'
    ],
    python_requires='>=3.8',
    setup_requires=['pytest-runner'],
    tests_require=['pytest-mypy'],
    extras_require={
        'future-regex': ['regex']
    },
)
