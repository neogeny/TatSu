# TatSuRDG
A random derivation generator for grammars that were compiled with the TatSu PEG/Packrat parser generator for Python.

A typical application is testing grammars by generating some derivations and checking if they look like intended. 

It is also possible to replace subrules of the grammar with constant (also empty) strings, so the derivations become more simple and more modular. 

Regex patterns are derived using the rstr package.