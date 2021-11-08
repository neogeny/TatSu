import tatsu.grammars
import random
import sys
import rstr


class RuleInfo:
    def __init__(self):
        self.max_counter = 0
        self.visit_counter = 0
        self.grammar = None


class TatSuRDG:
    """
    The class TatSuRDG provides a functionality to generate derivations of grammars
    compiled into a TatSu parser randomly
    """
    version = "1.0.2"

    def __init__(self, parser, max_length_regex=5, max_counter=5, recursion_limit=1000, override_placeholders=dict()):
        """
        :param parser: a compiled TatSu parser for some grammar
        :param max_length_regex: TatSuRDG will try to limit the derivations for all terminals of the grammar with a regex patterns to this length
        :param max_counter: While generating a derivation, TatSuRDG might 'visit' a choice rule (a|b|..) multiple times. TatSuRDG will select all options randomly until each has been chosen max_counter of times. From then on, TatSuRDG will select only the LAST option. Since TatSu parsers are PEG parsers, the last option is the 'most simple' one. max_counter prevents infinite derivations or derivations becoming too complex.
        :param recursion_limit: If you encounter RecursionError try to increase the default value for complex grammars.
        :param override_placeholders: Overrides the default derivations of single rules by deriving a placeholder for them. The dictionary is a key value list where the key is the name of the rule and the value is a string representing the placeholder.
        """
        self.parser = parser
        # dict of rules whose derivations will be replaced by placeholder values
        self.override_placeholders = override_placeholders
        self.max_counter = max_counter
        self.choice_rules = dict()
        self._visited = set()
        self.counters = dict()
        self.init_rules()
        self.max_length_regex = max_length_regex
        sys.setrecursionlimit(recursion_limit)
        print("TatSu Random Derivation Generator ({0}) initialized with {1}".format(self.version,
                                                                                    str(sys.getrecursionlimit())))

    def random_derivation(self, rule):
        self._visit(rule)
        if str(rule) in self.override_placeholders:
            return str(self.override_placeholders[str(rule)])
        if type(rule) is not str:
            # we have a tatsu grammars object
            tatsu_rule_object = rule
        else:
            # we have the name of the rule, for which we look for the tatsu grammar object
            if rule in self.parser.rulemap:
                tatsu_rule_object = self.parser.rulemap[rule]
            else:
                # e.g. 'something'
                return rule
        if type(tatsu_rule_object) is tatsu.grammars.Sequence:
            # e.g. "x y z"
            ret = ""
            for sequence_elem in tatsu_rule_object.sequence:
                ret += self.random_derivation(sequence_elem)
            return ret
        elif type(tatsu_rule_object) is tatsu.grammars.Pattern:
            # e.g. "/\d+/"
            r = rstr.xeger(rule.pattern)
            counter = 0
            while len(r) > self.max_length_regex and counter < 1000:
                counter += 1
                r = rstr.xeger(rule.pattern)
            if counter >= 1000:
                raise ValueError(
                    "Cannot derive instance of regex /{0}/ that is shorter than {1}".format(str(rule.pattern),
                                                                                            self.max_length_regex))
            else:
                return r
        elif type(tatsu_rule_object) is tatsu.grammars.Token:
            # e.g. "x" -> terminal !
            return tatsu_rule_object.token
        elif type(tatsu_rule_object) is tatsu.grammars.Constant:
            # e.g. "'TATSU'" -> terminal !
            return str(tatsu_rule_object.ast)
        elif type(tatsu_rule_object) is tatsu.grammars.Group:
            # e.g. (x)
            return self.random_derivation(tatsu_rule_object.exp)
        elif type(tatsu_rule_object) is tatsu.grammars.Choice:
            # e.g. (x | y)
            option = self.select_choice(str(tatsu_rule_object))
            return self.random_derivation(option)
        elif type(tatsu_rule_object) is tatsu.grammars.PositiveClosure:
            # e.g. { x }+ or
            r = random.randint(1, 3)
            ret = ""
            while r > 0:
                ret += self.random_derivation(tatsu_rule_object.exp)
                r -= 1
            return ret
        elif type(tatsu_rule_object) is tatsu.grammars.Named:
            # e.g. some_name:{x}+ or some_name:{x}*
            return self.random_derivation(tatsu_rule_object.exp)
        elif type(tatsu_rule_object) is tatsu.grammars.Closure:
            # e.g. { x }*
            r = random.randint(0, 2)
            ret = ""
            while r > 0:
                ret += self.random_derivation(tatsu_rule_object.exp)
                r -= 1
            return ret
        elif type(tatsu_rule_object) is tatsu.grammars.PositiveGather:
            # e.g. s.{ x }+
            r = random.randint(1, 3)
            ret = ""
            while r > 0:
                ret += self.random_derivation(tatsu_rule_object.JOINOP)
                ret += self.random_derivation(tatsu_rule_object.exp)
                r -= 1
            return ret
        elif type(tatsu_rule_object) is tatsu.grammars.RuleRef:
            # e.g. x
            # return the expansion of the referenced rule
            return self.random_derivation(tatsu_rule_object.ast)
        elif type(tatsu_rule_object) is tatsu.grammars.Rule:
            # e.g. x
            # return the expansion of the rule
            return self.random_derivation(tatsu_rule_object.exp)
        elif type(tatsu_rule_object) is tatsu.grammars.NamedList:
            # e.g. name+:x
            return self.random_derivation(tatsu_rule_object.exp)
        elif type(tatsu_rule_object) is tatsu.grammars.NegativeLookahead:
            # e.g. !x
            # TatSu parser will fail if x can be parsed but does not consume any input
            # we want derivations anyway
            return self.random_derivation(tatsu_rule_object.exp)
        elif type(tatsu_rule_object) is tatsu.grammars.Lookahead:
            # e.g. &x will succeed if x can be parsed but does not consume any input
            # we want derivations anyway
            return self.random_derivation(tatsu_rule_object.exp)
        elif type(tatsu_rule_object) is tatsu.grammars.Cut:
            # e.g. ~
            return ""  # ignore, since we are deriving already the option, other options are cut anyway
        elif type(tatsu_rule_object) is tatsu.grammars.Override:
            # e.g. y = '(' @:x ')' (makes the AST for y to be the AST for x
            # ignore, since we are interested not in the AST but in the syntactical derivations
            return self.random_derivation(tatsu_rule_object.exp)
        elif type(tatsu_rule_object) is tatsu.grammars.OverrideList:
            # e.g. y = '(' @+:x ')' (makes the AST for y to be the AST for x and forces it to be a list)
            # ignore, since we are interested not in the AST but in the syntactical derivations
            return self.random_derivation(tatsu_rule_object.exp)
        elif type(tatsu_rule_object) is tatsu.grammars.Optional:
            # e.g. [x]
            r = random.randint(0, 1)
            if r > 0:
                # chance 50% the option will be derived
                return self.random_derivation(tatsu_rule_object.exp)
            else:
                return ""
        elif type(tatsu_rule_object) is tatsu.grammars.Void:
            # e.g. ()
            return ""
        elif type(tatsu_rule_object) is tatsu.grammars.EOF:
            # $
            return ""
        elif type(tatsu_rule_object) is tatsu.grammars.RuleInclude:
            # e.g. >x
            # includable = exp1 ; expanded = exp0 >includable exp2; has the same effect as defining expanded as:
            # expanded = exp0 exp1 exp2;
            return self.random_derivation(tatsu_rule_object.exp)
        else:
            raise TypeError(str(type(tatsu_rule_object)))

    def _visit(self, tatsu_rule_object):
        self.counters[str(tatsu_rule_object)].visit_counter += 1

    def init_rules(self):
        self._visited.clear()
        for rule in self.parser.rulemap:
            self._init_rules_rek(rule)

    def _init_rules_rek(self, rule):
        rule_found = True
        if type(rule) is not str:
            # we have a tatsu grammars object
            tatsu_rule_object = rule
        else:
            if rule in self.parser.rulemap:
                # we have the name of the rule, for which we look for the tatsu grammar object
                tatsu_rule_object = self.parser.rulemap[rule]
            else:
                # the string was a TatSu constant or token.ast
                tatsu_rule_object = rule
                rule_found = False
        if str(tatsu_rule_object) in self._visited:
            return
        else:
            rule_name = str(rule)
            self._visited.add(rule_name)
            ri = RuleInfo()
            ri.max_counter = self.max_counter
            ri.grammar = tatsu_rule_object
            self.counters[rule_name] = ri
            if type(tatsu_rule_object) is tatsu.grammars.Constant or type(tatsu_rule_object) is str:
                # do not resolve constants any more
                return
        if rule_found:
            if type(tatsu_rule_object) is tatsu.grammars.Sequence:
                for sequence_elem in tatsu_rule_object.sequence:
                    self._init_rules_rek(sequence_elem)
            elif type(tatsu_rule_object) is tatsu.grammars.Pattern:
                return  # not a choice, no more recursive rules
            elif type(tatsu_rule_object) is tatsu.grammars.Token:
                self._init_rules_rek(tatsu_rule_object.ast)
            elif type(tatsu_rule_object) is tatsu.grammars.Group:
                # e.g. (x)
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.Choice:
                # e.g. (x | y)
                # choice found
                self.choice_rules[str(rule)] = rule
                for option in tatsu_rule_object.options:
                    self._init_rules_rek(option)
            elif type(tatsu_rule_object) is tatsu.grammars.PositiveClosure:
                # e.g. { x }+
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.PositiveGather:
                # e.g. s.{ x }+
                self._init_rules_rek(tatsu_rule_object.JOINOP)  # register s
                self._init_rules_rek(tatsu_rule_object.exp)  # register x
            elif type(tatsu_rule_object) is tatsu.grammars.Named:
                # e.g. some_name:{x}+
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.RuleRef:
                # e.g. x
                # return the expansion of the referenced rule
                self._init_rules_rek(tatsu_rule_object.ast)
            elif type(tatsu_rule_object) is tatsu.grammars.Rule:
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.EOF:
                return  # not a choice, no more recursive rules
            elif type(tatsu_rule_object) is tatsu.grammars.Closure:
                # e.g. { x }*
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.Constant:
                # e.g. 'TATSU'
                self._init_rules_rek(tatsu_rule_object.ast)
            elif type(tatsu_rule_object) is tatsu.grammars.NamedList:
                # e.g. name+:x
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.NegativeLookahead:
                # e.g. !x
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.Lookahead:
                # e.g. &x
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.Cut:
                # e.g. ~
                return
            elif type(tatsu_rule_object) is tatsu.grammars.Override:
                # e.g. y = '(' @:x ')' (makes the AST for y to be the AST for x)
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.OverrideList:
                # e.g. y = '(' @+:x ')' (makes the AST for y to be the AST for x and forces it to be a list)
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.Optional:
                # e.g. [x]
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.RuleInclude:
                # e.g. >x
                # includable = exp1 ; expanded = exp0 >includable exp2; has the same effect as defining expanded as:
                # expanded = exp0 exp1 exp2;
                self._init_rules_rek(tatsu_rule_object.exp)
            elif type(tatsu_rule_object) is tatsu.grammars.Void:
                # e.g. ()
                return
            else:
                raise TypeError(str(type(tatsu_rule_object)))
        else:
            # done
            pass

    def select_choice(self, rule_name):
        options = self._get_unvisited_options(rule_name)
        n = len(options)
        if n == 0:
            # if no more unvisited options (all options have been visited at least once)
            # return the last option. Since TatSu is a PEG parser, the last option is the "most simple one"
            return self.choice_rules[rule_name].options[-1]
        else:
            # select an option randomly based on the number of options, preferring the later ones
            return options[self.select_index_randomly(n)]

    def _get_unvisited_options(self, rule_name):
        options = []
        for option in self.choice_rules[rule_name].options:
            option_name = str(option)
            ri = self.counters[option_name]
            if ri.visit_counter < ri.max_counter:
                # add the option only if it was not yet visited the maximal times
                options.append(option)
        return options

    @staticmethod
    def select_index_randomly(n: int):
        if type(n) is not int:
            raise ValueError(str(n) + " must be a positive integer")
        elif n <= 0:
            raise ValueError(str(n) + " must be a positive integer")
        r = random.randint(1, n * (n + 1) // 2)
        i = 0
        total = 0
        while i <= n:
            i += 1
            total += i
            if total >= r:
                break
        if i > n:
            return None
        elif total >= r:
            return i - 1
        else:
            return None

    def _identify_options(self):
        ret = dict()
        for rule in self.parser.rulemap:
            if type(rule) is tatsu.grammars.Choice:
                ret[str(rule)] = rule
        return ret
