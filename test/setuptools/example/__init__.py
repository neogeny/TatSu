from . import parser


def parse(text):
    return parser.CALCParser().parse(text)
