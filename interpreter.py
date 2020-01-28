#!/usr/bin/env python3
import sys
from lark import Lark

import kernel
import datastore
from undefined import Undefined
from function import Function
from lark import Tree
from lark import Token

from test_interpreter import get_test_cases
from test_interpreter import Skip

class Interpreter(object):
  def __init__(self, grammar_file_name, debug=False):
    with open(grammar_file_name, 'r') as grammar_file:
      grammar = grammar_file.read()
    if not grammar:
      raise ValueError('grammar file renamed or missing!')
    self.parser = Lark(grammar, start='start', parser='earley')
    self.debug  = debug
  
  def execute(self, command, user, server):
    tree = self.parser.parse(command)
    if self.debug:
      print(tree, '\n')
    return self.interpret(tree, user, server)
    
  def interpret(self, tree, user, server):
    return kernel.handle_instruction(tree, user, server)


def main(*args):
  args = list(args)
  no_expected = '--no-test' in args
  if no_expected:
    args.pop(args.index('--no-test'))
  try:
    filename = args[1]
  except IndexError:
    print('No filename provided!')
    return 1
  test_cases = get_test_cases(filename, no_expected)
  interpreter = Interpreter('grammar.lark')
  for command, expected in test_cases:
    print(command)
    actual = interpreter.execute(command, 'Tester', 'Test Server')
    if no_expected:
      print(command, '===>', actual)
    elif expected is not Skip
      if actual != expected:
        print('actual = {}\n expected = {}'.format(actual, expected))
      assert actual == expected
    else:
      assert True
  return 0

if __name__ == '__main__':
  exit_code = main(*sys.argv)
  sys.exit(exit_code)
  
