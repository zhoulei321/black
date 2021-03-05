# Copyright 2004-2005 Elemental Security, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Parser engine for the grammar tables generated by pgen.

The grammar table must be loaded first.

See Parser/parser.c in the Python distribution for additional info on
how this parsing engine works.

"""

# Local imports
from . import token
from typing import (
    Optional,
    Text,
    Union,
    Tuple,
    Dict,
    List,
    Callable,
    Set
)
from blib2to3.pgen2.grammar import Grammar
from blib2to3.pytree import NL, Context, RawNode, Leaf, Node


Results = Dict[Text, NL]
Convert = Callable[[Grammar, RawNode], Union[Node, Leaf]]
DFA = List[List[Tuple[int, int]]]
DFAS = Tuple[DFA, Dict[int, int]]


def lam_sub(grammar: Grammar, node: RawNode) -> NL:
    assert node[3] is not None
    return Node(type=node[0], children=node[3], context=node[2])


class ParseError(Exception):
    """Exception to signal the parser is stuck."""

    def __init__(
        self, msg: Text, type: Optional[int], value: Optional[Text], context: Context
    ) -> None:
        Exception.__init__(
            self, "%s: type=%r, value=%r, context=%r" % (msg, type, value, context)
        )
        self.msg = msg
        self.type = type
        self.value = value
        self.context = context


class Parser(object):
    """Parser engine.

    The proper usage sequence is:

    p = Parser(grammar, [converter])  # create instance
    p.setup([start])                  # prepare for parsing
    <for each input token>:
        if p.addtoken(...):           # parse a token; may raise ParseError
            break
    root = p.rootnode                 # root of abstract syntax tree

    A Parser instance may be reused by calling setup() repeatedly.

    A Parser instance contains state pertaining to the current token
    sequence, and should not be used concurrently by different threads
    to parse separate token sequences.

    See driver.py for how to get input tokens by tokenizing a file or
    string.

    Parsing is complete when addtoken() returns True; the root of the
    abstract syntax tree can then be retrieved from the rootnode
    instance variable.  When a syntax error occurs, addtoken() raises
    the ParseError exception.  There is no error recovery; the parser
    cannot be used after a syntax error was reported (but it can be
    reinitialized by calling setup()).

    """

    def __init__(self, grammar: Grammar, convert: Optional[Convert] = None) -> None:
        """Constructor.

        The grammar argument is a grammar.Grammar instance; see the
        grammar module for more information.

        The parser is not ready yet for parsing; you must call the
        setup() method to get it started.

        The optional convert argument is a function mapping concrete
        syntax tree nodes to abstract syntax tree nodes.  If not
        given, no conversion is done and the syntax tree produced is
        the concrete syntax tree.  If given, it must be a function of
        two arguments, the first being the grammar (a grammar.Grammar
        instance), and the second being the concrete syntax tree node
        to be converted.  The syntax tree is converted from the bottom
        up.

        A concrete syntax tree node is a (type, value, context, nodes)
        tuple, where type is the node type (a token or symbol number),
        value is None for symbols and a string for tokens, context is
        None or an opaque value used for error reporting (typically a
        (lineno, offset) pair), and nodes is a list of children for
        symbols, and None for tokens.

        An abstract syntax tree node may be anything; this is entirely
        up to the converter function.

        """
        self.grammar = grammar
        self.convert = convert or lam_sub

    def setup(self, start: Optional[int] = None) -> None:
        """Prepare for parsing.

        This *must* be called before starting to parse.

        The optional argument is an alternative start symbol; it
        defaults to the grammar's start symbol.

        You can use a Parser instance to parse any number of programs;
        each time you call setup() the parser is reset to an initial
        state determined by the (implicit or explicit) start symbol.

        """
        if start is None:
            start = self.grammar.start
        # Each stack entry is a tuple: (dfa, state, node).
        # A node is a tuple: (type, value, context, children),
        # where children is a list of nodes or None, and context may be None.
        newnode: RawNode = (start, None, None, [])
        stackentry = (self.grammar.dfas[start], 0, newnode)
        self.stack: List[Tuple[DFAS, int, RawNode]] = [stackentry]
        self.rootnode: Optional[NL] = None
        self.used_names: Set[str] = set()

    def addtoken(self, type: int, value: Optional[Text], context: Context) -> bool:
        """Add a token; return True iff this is the end of the program."""
        # Map from token to label
        ilabel = self.classify(type, value, context)
        # Loop until the token is shifted; may raise exceptions
        while True:
            dfa, state, node = self.stack[-1]
            states, first = dfa
            arcs = states[state]
            # Look for a state with this label
            for i, newstate in arcs:
                t, v = self.grammar.labels[i]
                if ilabel == i:
                    # Look it up in the list of labels
                    assert t < 256
                    # Shift a token; we're done with it
                    self.shift(type, value, newstate, context)
                    # Pop while we are in an accept-only state
                    state = newstate
                    while states[state] == [(0, state)]:
                        self.pop()
                        if not self.stack:
                            # Done parsing!
                            return True
                        dfa, state, node = self.stack[-1]
                        states, first = dfa
                    # Done with this token
                    return False
                elif t >= 256:
                    # See if it's a symbol and if we're in its first set
                    itsdfa = self.grammar.dfas[t]
                    itsstates, itsfirst = itsdfa
                    if ilabel in itsfirst:
                        # Push a symbol
                        self.push(t, self.grammar.dfas[t], newstate, context)
                        break  # To continue the outer while loop
            else:
                if (0, state) in arcs:
                    # An accepting state, pop it and try something else
                    self.pop()
                    if not self.stack:
                        # Done parsing, but another token is input
                        raise ParseError("too much input", type, value, context)
                else:
                    # No success finding a transition
                    raise ParseError("bad input", type, value, context)

    def classify(self, type: int, value: Optional[Text], context: Context) -> int:
        """Turn a token into a label.  (Internal)"""
        if type == token.NAME:
            # Keep a listing of all used names
            assert value is not None
            self.used_names.add(value)
            # Check for reserved words
            ilabel = self.grammar.keywords.get(value)
            if ilabel is not None:
                return ilabel
        ilabel = self.grammar.tokens.get(type)
        if ilabel is None:
            raise ParseError("bad token", type, value, context)
        return ilabel

    def shift(
        self, type: int, value: Optional[Text], newstate: int, context: Context
    ) -> None:
        """Shift a token.  (Internal)"""
        dfa, state, node = self.stack[-1]
        assert value is not None
        assert context is not None
        rawnode: RawNode = (type, value, context, None)
        newnode = self.convert(self.grammar, rawnode)
        if newnode is not None:
            assert node[-1] is not None
            node[-1].append(newnode)
        self.stack[-1] = (dfa, newstate, node)

    def push(self, type: int, newdfa: DFAS, newstate: int, context: Context) -> None:
        """Push a nonterminal.  (Internal)"""
        dfa, state, node = self.stack[-1]
        newnode: RawNode = (type, None, context, [])
        self.stack[-1] = (dfa, newstate, node)
        self.stack.append((newdfa, 0, newnode))

    def pop(self) -> None:
        """Pop a nonterminal.  (Internal)"""
        popdfa, popstate, popnode = self.stack.pop()
        newnode = self.convert(self.grammar, popnode)
        if newnode is not None:
            if self.stack:
                dfa, state, node = self.stack[-1]
                assert node[-1] is not None
                node[-1].append(newnode)
            else:
                self.rootnode = newnode
                self.rootnode.used_names = self.used_names
