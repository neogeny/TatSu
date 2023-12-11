from ..objectmodel import ParseModel
from .python import PythonCodeGenerator


def codegen(model: ParseModel, parser_name: str = '') -> str:
    generator = PythonCodeGenerator(parser_name=parser_name)
    generator.walk(model)
    return generator.printed_text()
