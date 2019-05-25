import argparse

from .import filelist_from_patterns
from .parproc import processing_loop


def parallel_test_run(parse, patterns, sizesort=True, reraise=False, excludes=None, base=None, **kwargs):
    try:
        filenames = filelist_from_patterns(patterns, base=base, sizesort=sizesort, excludes=excludes)
        return processing_loop(parse, filenames, reraise=reraise, **kwargs)
    except KeyboardInterrupt:
        if reraise:
            raise


def parse_args():
    argparser = argparse.ArgumentParser(
        prog=__package__,
        # description=DESCRIPTION,
        add_help=False,
    )

    argparser.add_argument(
        'patterns',
        nargs='+',
        metavar='PATTERNS',
        help='filename patterns',
    )
    argparser.add_argument(
        '--reraise', '-r',
        help='show complete stack trace for exceptions',
        action='store_true',
    )
    argparser.add_argument(
        '--sort', '-s',
        help='sort files by size',
        action='store_true',
    )
    argparser.add_argument(
        '--serial', '-S',
        help='do not run in parallel',
        action='store_true',
    )
    argparser.add_argument(
        '--trace', '-t',
        help='produce verbose output for a parse',
        action='store_true',
    )
    argparser.add_argument(
        '--exclude', '-x',
        metavar='PATTERN',
        help='exclude these patterns',
        action='append',
    )
    argparser.add_argument(
        '--help', '-h',
        help='show this help message and exit',
        action='help',
    )
    return argparser.parse_args()


def generic_main(parse):
    args = parse_args()
    return parallel_test_run(
        parse,
        args.patterns,
        reraise=args.reraise,
        trace=args.trace,
        parallel=not args.serial,
        sizesort=args.sort,
        excludes=args.exclude,
    )
