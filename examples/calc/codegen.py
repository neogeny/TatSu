import sys

from tatsu.model import Node
from tatsu.walkers import NodeWalker
from tatsu.mixins.indent import IndentPrintMixin


THIS_MODULE = sys.modules[__name__]


class PostfixCodeGenerator(NodeWalker, IndentPrintMixin):

    def walk_Number(self, node: Node):
        self.print(f'PUSH {self.walk(node.value)}')  # type: ignore


    def walk_Add(self, node: Node, *args, **kwargs):
        self.walk(node.left)  # type: ignore
        self.walk(node.right)  # type: ignore
        print('ADD')


    def walk_Subtract(self, node: Node, *args, **kwargs):
        self.walk(node.left)  # type: ignore
        self.walk(node.right)  # type: ignore
        print('SUB')


    def walk_Multiply(self, node: Node, *args, **kwargs):
        self.walk(node.left)  # type: ignore
        self.walk(node.right)  # type: ignore
        print('MUL')

    def walk_Divide(self, node: Node, *args, **kwargs):
        self.walk(node.left)  # type: ignore
        self.walk(node.right)  # type: ignore
        print('DIV')

    def walk_int(self, node:Node, *args, **kwargs):
        print('PUSH', node)
