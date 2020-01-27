#!/usr/bin/env python3
import sys
from lark import Lark

import kernel
import datastore
from undefined import Undefined
from function import Function
from lark import Tree
from lark import Token

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


def get_test_cases(filename, no_expected=False):
  '''test cases file pointed to by filename must have the following properties:
    * lines are either blank or contain a test case
    * test cases consist of three things in the following order:
      * the command to be executed by the dicelang interpreter
      * the exact sequence of characters '===>' without quotes
      * the value in Python to which the command should resolve'''
  test_cases = [ ]
  prepare = lambda s: s if no_expected else eval
  with open(filename, 'r') as f:
    for line in f:
      line = line.strip()
      if line:
        command, expected = map(lambda s: s.strip(), line.split('===>'))
        test_cases.append((command, prepare(expected)))
  return test_cases 

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
    else:
      if actual != expected:
        print('actual = {}\n expected = {}'.format(actual, expected))
      assert actual == expected
  return 0

if __name__ == '__main__':
  exit_code = main(*sys.argv)
  sys.exit(exit_code)
  
