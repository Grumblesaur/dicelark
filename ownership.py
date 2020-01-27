class ScopingData(object):
  def __init__(self, user='', server=''):
    self.user = user
    self.server = server
    self.scopes = [ ]
  
  def clear_params(self):
    self.set_params('', '')
  
  def depth(self):
    return len(self.scopes)
  
  def __bool__(self):
    return self.depth() > 0
  
  def __len__(self):
    return self.depth()
  
  def push_scope(self):
     self.scopes.append({})
  
  def pop_scope(self):
    return self.scopes.pop()
  
  def get(self, key):
    i = self.depth() - 1
    out = None
    while i >= 0:
      try:
        out = self.scopes[i][key]
      except KeyError:
        out = None
      i -= 1
    return out
  
  def put(self, key, value):
    self.scopes[-1][key] = value
    return value
  
  def drop(self, key):
    try:
      out = self.scopes[-1][key]
      del   self.scopes[-1][key]
    except KeyError:
      out = Undefined
    return out
  
  def __repr__(self):
    return 'ScopingData({usr}, {svr}, {scp})'.format(
      usr=repr(self.user),
      svr=repr(self.server),
      scp=repr(self.scopes))


