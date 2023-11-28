from ..objectmodel import ParseModel

from .python import PythonCodeGenerator


def codegen(model: ParseModel) -> str:
    generator = PythonCodeGenerator()
    generator.walk(model)
    return generator.printed_text()
