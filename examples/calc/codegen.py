import sys

from tatsu.model import Node
from tatsu.walkers import NodeWalker
from tatsu.mixins.indent import IndentPrintMixin


THIS_MODULE = sys.modules[__name__]


class PostfixCodeGenerator(NodeWalker, IndentPrintMixin):

    def walk_Add(self, node: Node, *args, **kwargs):
        with self.indent():
            self.walk(node.left)  # type: ignore
            self.walk(node.right)  # type: ignore
            self.print('ADD')

    def walk_Subtract(self, node: Node, *args, **kwargs):
        with self.indent():
            self.walk(node.left)  # type: ignore
            self.walk(node.right)  # type: ignore
            self.print('SUB')

    def walk_Multiply(self, node: Node, *args, **kwargs):
        with self.indent():
            self.walk(node.left)  # type: ignore
            self.walk(node.right)  # type: ignore
            self.print('MUL')

    def walk_Divide(self, node: Node, *args, **kwargs):
        with self.indent():
            self.walk(node.left)  # type: ignore
            self.walk(node.right)  # type: ignore
            self.print('DIV')

    def walk_int(self, node: Node, *args, **kwargs):
        self.print('PUSH', node)
