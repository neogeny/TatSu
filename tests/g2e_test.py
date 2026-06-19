import unittest

from tatsu import g2e, peg as g


class G2ETests(unittest.TestCase):
    def test_simple_parser_rule(self):
        model = g2e.translate(text="grammar T; start: 'hello';", name='T')
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('start', model.rulemap)

    def test_token_ref_after_definition(self):
        model = g2e.translate(text="grammar T; INT: [0-9]+; start: INT;", name='T')
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('INT', model.rulemap)
        self.assertIn('start', model.rulemap)

    def test_token_ref_before_definition(self):
        model = g2e.translate(text="grammar T; start: INT; INT: [0-9]+;", name='T')
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('INT', model.rulemap)
        self.assertIn('start', model.rulemap)

    def test_undefined_token_becomes_fail(self):
        model = g2e.translate(text="grammar T; start: INT;", name='T')
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('INT', model.rulemap)
        self.assertIsInstance(model.rulemap['INT'].exp, g.Fail)

    def test_camel_case_conversion(self):
        model = g2e.translate(
            text="grammar T; parseExpression: 'expr'; parseStatement: 'stmt';",
            name='T',
        )
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('parse_expression', model.rulemap)
        self.assertIn('parse_statement', model.rulemap)

    def test_tokens_block_unreferenced(self):
        model = g2e.translate(
            text="grammar T; tokens { DUMMY } start: 'x';",
            name='T',
        )
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('start', model.rulemap)

    def test_tokens_block_with_reference(self):
        model = g2e.translate(
            text="grammar T; tokens { INT } start: INT;",
            name='T',
        )
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('INT', model.rulemap)
        # `tokens { INT }` creates a Void() rule, taking precedence over Fail
        self.assertIsInstance(model.rulemap['INT'].exp, g.Void)

    def test_multiple_alternatives(self):
        model = g2e.translate(
            text="grammar T; start: 'a' | 'b' | 'c';",
            name='T',
        )
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('start', model.rulemap)

    def test_sequence_and_choice(self):
        model = g2e.translate(
            text="grammar T; start: 'a' 'b' ('c' | 'd');",
            name='T',
        )
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('start', model.rulemap)

    def test_optional_and_closure(self):
        model = g2e.translate(
            text="grammar T; start: 'a' ('b')* 'c'?;",
            name='T',
        )
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('start', model.rulemap)

    def test_pretty_output_is_valid(self):
        model = g2e.translate(
            text="grammar T; INT: [0-9]+; start: INT;",
            name='T',
        )
        pretty = model.pretty()
        self.assertIn('INT', pretty)
        self.assertIn('start', pretty)

    def test_grammar_name(self):
        model = g2e.translate(text="grammar Test; start: 'x';", name='Test')
        self.assertEqual(model.name, 'Test')

    def test_named_elements(self):
        model = g2e.translate(
            text="grammar T; start: name='x';",
            name='T',
        )
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('start', model.rulemap)

    def test_negative_lookahead(self):
        model = g2e.translate(
            text="grammar T; start: ~'x' 'y';",
            name='T',
        )
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('start', model.rulemap)

    def test_empty_grammar(self):
        model = g2e.translate(text="grammar T; start: ;", name='T')
        self.assertIsInstance(model, g.Grammar)
        self.assertIn('start', model.rulemap)

    def test_token_rule_becomes_fail(self):
        model = g2e.translate(
            text="grammar T; INT: [0-9]+;",
            name='T',
        )
        self.assertIsInstance(model.rulemap['INT'].exp, g.Fail)

    def test_fragment_rule_becomes_fail(self):
        model = g2e.translate(
            text="grammar T; fragment DIGIT: [0-9]; fragment LETTER: [a-z]; ID: (LETTER|DIGIT)+;",
            name='T',
        )
        self.assertIsInstance(model.rulemap['DIGIT'].exp, g.Fail)
        self.assertIsInstance(model.rulemap['LETTER'].exp, g.Fail)
        self.assertIsInstance(model.rulemap['ID'].exp, g.Fail)

    def test_token_rule_with_alternatives_becomes_fail(self):
        model = g2e.translate(
            text="grammar T; LETTER: [a-z] | [A-Z] | '_';",
            name='T',
        )
        self.assertIsInstance(model.rulemap['LETTER'].exp, g.Fail)

    def test_forward_ref_token_rule_becomes_fail(self):
        model = g2e.translate(
            text="grammar T; ID: STD_CONTINUE* STD_START; fragment STD_START: [a-z] | '_'; fragment STD_CONTINUE: [a-z] | [0-9];",
            name='T',
        )
        self.assertIsInstance(model.rulemap['ID'].exp, g.Fail)
        self.assertIsInstance(model.rulemap['STD_START'].exp, g.Fail)
        self.assertIsInstance(model.rulemap['STD_CONTINUE'].exp, g.Fail)

    def test_token_rule_unicode_escapes(self):
        model = g2e.translate(
            text="grammar T; UNI: '\\u00AA' | '\\u00B5';",
            name='T',
        )
        self.assertIsInstance(model.rulemap['UNI'].exp, g.Fail)

    def test_token_rule_positive_closure(self):
        model = g2e.translate(
            text="grammar T; fragment DIGIT: [0-9]; FLOAT: DIGIT+ '.' DIGIT+;",
            name='T',
        )
        self.assertIsInstance(model.rulemap['DIGIT'].exp, g.Fail)
        self.assertIsInstance(model.rulemap['FLOAT'].exp, g.Fail)


if __name__ == '__main__':
    unittest.main()
