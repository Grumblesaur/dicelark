import lark
import handlers

def handle_instruction(tree):
  if tree.data == 'start':
    out = handle_instruction(tree.children[0])
  
  elif tree.data == 'expression':
    out = handle_instruction(tree.children[0])
  elif tree.data == 'simple_assignment':
    print(tree.children)
    out = tree.data
  
  elif tree.data == 'bool_or':
    out = handle_instruction(tree.children[0])
  elif tree.data == 'logical_or':
    print(tree.children)
    out = tree.data
  
  elif tree.data == 'bool_xor':
    out = handle_instruction(tree.children[0])
  elif tree.data == 'logical_xor':
    print(tree.children)
    out = tree.data
  
  elif tree.data == 'bool_and':
    out = handle_instruction(tree.children[0])
  elif tree.data == 'logical_and':
    print(tree.children)
    out = tree.data
  
  elif tree.data == 'bool_not':
    out = handle_instruction(tree.children[0])
  elif tree.data == 'logical_not':
    print(tree.children)
    out = tree.data
  
  elif tree.data == 'comp':
    out = handle_instruction(tree.children[0])
  elif tree.data == 'greater_than':
    print(tree.children)
    out = tree.data
  elif tree.data == 'greater_equal':
    print(tree.children)
    out = tree.data
  elif tree.data == 'equal':
    print(tree.children)
    out = tree.data
  elif tree.data == 'not_equal':
    print(tree.children)
    out = tree.data
  elif tree.data == 'less_equal':
    print(tree.children)
    out = tree.data
  elif tree.data == 'less_than':
    print(tree.children)
    out = tree.data
  
  elif tree.data == 'shift':
    out = handle_instruction(tree.children[0])
  elif tree.data == 'left_shift':
    print(tree.children)
    out = tree.data
  elif tree.data == 'right_shift':
    print(tree.children)
    out = tree.data
  
  elif tree.data == 'arithm':
    out = handle_instruction(tree.children[0])
  elif tree.data == 'addition':
    print(tree.children)
    out = tree.data
  elif tree.data == 'subtraction':
    print(tree.children)
    out = tree.data
  elif tree.data == 'catenation':
    print(tree.children)
    out = tree.data
  
  elif tree.data == 'term':
    out = handle_instruction(tree.children[0])
  elif tree.data == 'multiplication':
    print(tree.children)
    out = tree.data
  elif tree.data == 'division':
    print(tree.children)
    out = tree.data
  elif tree.data == 'remainder':
    print(tree.children)
    out = tree.data
  elif tree.data == 'floor_division':
    print(tree.children)
    out = tree.data
  
  elif tree.data == 'factor':
    out = handle_instruction(tree.children[0])
  elif tree.data == 'negation':
    print(tree.children)
    out = tree.data
  elif tree.data == 'idempotence':
    print(tree.children)
    out = tree.data
  
  elif tree.data == 'power':
    out = handle_instruction(tree.children[0])
  elif tree.data == 'exponent':
    out = handlers.handle_power(tree.children)
  elif tree.data == 'logarithm':
    out = handlers.handle_logarithm(tree.children)
  
  elif tree.data == 'die':
    out = handle_instruction(tree.children[0])
  elif 'scalar_die' in tree.data or 'vector_die' in tree.data:
    out = handlers.handle_dice(tree.data, tree.children)
  
  elif tree.data == 'atom':
    child = tree.children[0]
    out = handlers.handle_atom(child)
  elif tree.data == 'populated_list':
    out = handlers.handle_list(tree.children)
  elif tree.data == 'empty_list':
    out = handlers.handle_list(None)
  else:
    print(tree.data)
    out = '__UNIMPLEMENTED__'
  
  return out


