import argparse


def print_parser_tree(parser, indent=0):
    prefix = "  " * indent
    # Print the name of the parser or command
    print(f"{prefix}Command: {parser.prog}")

    # Print arguments for this level
    for action in parser._actions:
        if not isinstance(action, (argparse._HelpAction, argparse._SubParsersAction)):
            print(f"{prefix}  - {action.option_strings}")

    # Recurse into subparsers
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for choice, subparser in action.choices.items():
                print(f"{prefix}Subcommand: {choice}")
                print_parser_tree(subparser, indent + indent + 1)


# Usage:
# print_parser_tree(parser)
