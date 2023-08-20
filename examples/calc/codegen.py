import sys

from tatsu.model import Node
from tatsu.walkers import NodeWalker
from tatsu.mixins.indent import IndentPrintMixin
from tatsu.codegen import ModelRenderer

THIS_MODULE = sys.modules[__name__]


class PostfixCodeGenerator(NodeWalker, IndentPrintMixin):

    def walk_Number(self, node: Node):
        self.print(f'PUSH {self.walk(node.value)}')


    def walk_Add(self, node: Node, *args, **kwargs):
        self.walk(node.left)
        self.walk(node.right)
        print('ADD')


    def walk_Subtract(self, node: Node, *args, **kwargs):
        self.walk(node.left)
        self.walk(node.right)
        print('SUB')


    def walk_Multiply(self, node: Node, *args, **kwargs):
        self.walk(node.left)
        self.walk(node.right)
        print('MUL')

    def walk_Divide(self, node: Node, *args, **kwargs):
        self.walk(node.left)
        self.walk(node.right)
        print('DIV')

    def walk_int(self, node:Node, *args, **kwargs):
        print('PUSH', node)


