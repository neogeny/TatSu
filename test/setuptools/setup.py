from setuptools import setup

setup(
    name="example",
    version="0.1",
    author='TatSu',
    author_email='tatsu@example.net',
    url='https://github.com/neogeny/TatSu/tree/master/test/setuptools/',
    packages=["example"],
    setup_requires=["tatsu>=5.8.2"],
    tatsu_parsers=[
        "example/calc.ebnf:example.parser",
    ],
    install_requires=["tatsu>=5.8.2"],
)
