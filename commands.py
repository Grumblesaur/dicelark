import re
import enum
import lark
import discord
from lark import UnexpectedToken, UnexpectedCharacters, UnexpectedInput

import helptext
from dicelang import interpreter
from dicelang.exceptions import DicelangError
from result_file import ResultFile

syntax = r'''
  start: "+" ("atropos")? command
  command: roll -> command_roll
         | view -> command_view
         | help -> command_help
  
  roll: "roll" /(.|\n)+/  -> roll_code
      | "lit" /(.|\n)+/ -> roll_lit
      | "roll"            -> roll_help
  
  view: "view"    "all"   ("vars")?                  -> view_all
      | "view" (( "global" ("vars")?) | "globals"  ) -> view_public
      | "view" (( "our"    ("vars")?) | "shareds"  ) -> view_shared
      | "view" (( "my"     ("vars")?) | "privates" ) -> view_private
      | "view" (( "core"   ("vars")?) | "library"  ) -> view_core
      | "view" (/\w+/)?                              -> view_help
  
  help: "help" /\b\w+\b/+ -> help_topic
      | "help"            -> help_help
  
  %import common.WS
  %ignore WS
'''

class CommandType:
  error = 'error'
  roll_code = 'roll_code'
  roll_lit  = 'roll_lit'
  roll_help = 'roll_help'
  view_all  = 'view_all'
  view_public = 'view_public'
  view_shared = 'view_shared'
  view_private = 'view_private'
  view_core = 'view_core'
  view_help = 'view_help'
  help_topic = 'help_topic'
  help_help = 'help_help'
  
  pass_by = ['start', 'command_roll', 'command_view', 'command_help']
  views = [
    view_public, view_private,
    view_core,   view_shared,
    view_help,   view_all,
  ]
  
  no_args = views + [help_help] + [roll_help]
  
  helps = [help_help, help_topic]

class Builder(object):
  def __init__(self, dicelang_interpreter, helptext_engine):
    self.dicelang = dicelang_interpreter
    self.helptable = helptext_engine
  
  def get_server_id(self, msg):
    if isinstance(msg.channel, (discord.GroupChannel, discord.DMChannel)):
      return msg.channel.id
    return msg.channel.guild.id
  
  def view_reply(self, command_type, msg):
    server_id = self.get_server_id(msg)
    user_id = msg.author.id
    cores, pubs, servs, privs = ('',) * 4
    sep = '  '
    if command_type in (CommandType.view_public, CommandType.view_all):
      pubs = sep.join(self.dicelang.keys('global'))
    if command_type in (CommandType.view_shared, CommandType.view_all):
      servs = sep.join(self.dicelang.keys('server', server_id))
    if command_type in (CommandType.view_private, CommandType.view_all):
      privs = sep.join(self.dicelang.keys('private', user_id))
    if command_type in (CommandType.view_core, Commandtype.view_all):
      cores = sep.join(self.dicelang.keys('core'))
    
    if command_type == CommandType.view_help:
      options = 'all core global my our'.split()
      return {
        'action' : 'Possible options',
        'result' : '\n'.join(map(lambda o: f'  {o}', options))
        'help'   : True,
      }
    
    content = 'Variables:\n'
    if cores:
      content += f'  CORE:\n    {cores}\n'
    if pubs:
      content += f'  GLOBALS:\n    {pubs}\n'
    if servs:
      content += f'  SHAREDS:\n    {servs}\n'
    if privs:
      content += f'  PRIVATES:\n    {privs}'
    
    action = f'{msg.author.display_name} requested to view:\n'
    result = f'```{content}```'
    return {'action' : action, 'result' : result, 'help' : False}
      
  
  def dice_reply(self, code, msg):
    server_id = self.get_server_id(msg)
    act, res = '', ''
    error = True
    try:
      res, act = self.dicelang.execute(code, msg.author.id, server_id)
    except (UnexpectedCharacters, UnexpectedToken, UnexpectedInput) as e:
      res = e.get_context(code, max(15, len(code) // 10))
      act = 'Syntax Error'
    except UnexpectedEOF as e:
      res = str(e).split('.')[0] + '.'
      act = 'Unexpected End of Input'
    except (ParseError, LexError) as e:
      res = f'{e!s}'
      act = 'Lexer/Parser Error'
    except NameError as e:
      res = 'Missing internal identifier: {e!s}'
      act = 'Interpreter Error'
      traceback.print_tb(e.__traceback__)
    except DicelangError as e:
      act = self.dicelang.get_print_queue_on_error(msg.author.id)
      classname = e.__class__.__name__
      try:
        res = f'{classname}: {e.msg}'
      except AttributeError:
        res = f'{classname}: {e.args[0]!s}'
    except Exception as e:
      act = self.dicelang.get_print_queue_on_error(msg.author.id)
      res = f'{e.__class__.__name__}: {e!s}'
      traceback.print_tb(e.__traceback__)
    else:
      error = False
    return {'action': act, 'result': res, 'error': error}

  def help_reply(self, argument, option, meta=False):
    reply_data = { }
    if meta:
      reply_data['action'] = 'Possible topics'
      reply_data['result'] = ''.join(
        self.helptable.lookup('help', None),
        self.helptable.lookup('topics', None)
      )
    else:
      optstring = (' ' + option) if option else ''
      reply_data['action'] = f'Help for `{argument}{optstring}`'
      reply_data['result'] = self.helptable.lookup(argument, option)
    return reply_data

class Command(object):
  pkw = {'start':'start', 'parser':'earley', 'lexer':'dynamic_complete'}
  parser = lark.Lark(syntax, **pkw)
  builder = Builder(interpreter.Interpreter(), helptext.HelpText())
  
  def __init__(self, message):
    parser_output = self.parse(message.content)
    if parser_output['error']:
      self.type = CommandType.error
      self.kwargs = {}
    else:
      self.type, self.kwargs = self.visit(parser_output['tree'])
    self.originator = message
  
  def __repr__(self):
    return f'{self.__class__.__name__}<{self.type}:{self.kwargs!r}>'
  
  def __bool__(self):
    return not self.type == CommandType.error
  
  def get_client_alias(self, msg, client):
    try:
      for user in msg.channel.members:
        if user.id == client.user.id:
          return user.display_name
    except AttributeError:
      pass
    return 'Atropos'
    
  def parse(self, message_text):
    try:
      tree_or_error = self.__class__.parser.parse(message_text)
    except (UnexpectedCharacters, UnexpectedToken, UnexpectedInput) as e:
      tree_or_error = e.get_context(message_text, 20)
      error = True
    except Exception as e:
      tree_or_error = e
      error = True
    else:
      error = False
    return {'error' : error, 'tree' : tree_or_error}

  def visit(self, tree):
    if tree.data in CommandType.pass_by:
      out = self.visit(tree.children[0])
    elif tree.data in CommandType.no_args:
      out = tree.data, {}
    elif tree.data == CommandType.roll_code:
      out = tree.data, {'value': tree.children[0].value}
    elif tree.data == CommandType.roll_lit:
      out = tree.data, {'value': tree.children[0].value, 'option': 'literate'}
    elif tree.data == CommandType.help_topic:
      option = tree.children[1].value if len(tree.children) > 1 else ''
      out = tree.data, {'value': tree.children[0].value, 'option': option}
    else:
      out = tree.data, {'value': f'UNIMPLEMENTED: {tree.data}'}
    return out

  async def send_reply_as(self, client):
    if not self:
      return
    async with self.originator.channel.typing():
      await self.reply(client)
  
  
  async def reply(self, client):
    '''Construct a reply for the type of command we are. If no valid
    Command type was identified, this function is a no-op.'''
    if not self:
      return
    
    username = self.originator.author.display_name
    if self.type == CommandType.roll_code:
      d = Command.builder.dice_reply(self.kwargs['value'], self.originator)
      action = d['action']
      result = d['result']
      error = d['error'] * ' error'
      c = f'{username} received{error}:\n'
      if d['action']:
        c += f'```{action}```\n'
      c += f'```{result}```'
      reply = {'content' : c}
      
    elif self.type == CommandType.roll_lit:
      d = Command.builder.dice_reply(self.kwargs['value'], self.originator)
      action = d['action']
      result = d['result']
      error = 'Error' if d['error'] else 'Roll'
      embed_kw = {
        'title' : f'{error} result for {username}',
        'description': f'```{self.originator.content}```',
        'color' : self.originator.author.color,
      }
      embed = discord.Embed(**embed_kw)
      if action:
        embed.add_field(name='Action', value=f'```{action}```', inline=False)
      embed.add_field(name='Result', value=f'```{result}```', inline=False)
      reply = {'embed' : embed}
      
    elif self.type == CommandType.roll_help:
      reply = {'content' : 'See `+atropos help quickstart` for more info.'}
      
    elif self.type in CommandType.views:
      embed_fields = Command.builder.view_reply(self.type, self.originator)
      noun = 'help' if embed_fields['help'] else 'view'
      title = f'Database {noun} for {username}'
      embed_kw = {
        'title' : title,
        'description' : f'```{self.originator.content}```',
        'color' : self.originator.author.color,
      }
      embed = discord.Embed(**embed_kw)
      embed.add_field(name='Action', value=embed_fields["action"], inline=False)
      embed.add_field(name='Result', value=embed_fields["result"], inline=False)
      reply = {'embed' : embed}
      
    elif self.type in CommandType.helps:
      data = Command.builder.help_reply(
        self.kwargs.get('value', None),
        self.kwargs.get('option', None),
        self.type == CommandType.help_help
      )
      embed_kw = {
        'title' : f'Help for {username}',
        'description' : f'```{self.originator.content}```',
        'color' : self.originator.author.color,
      }
      embed = discord.Embed(**embed_kw)
      embed.add_field(name='Action', value=data['action'], inline=False)
      embed.add_field(name='Result', value=data['result'], inline=False)
      reply = {'embed' : embed}
    else:
      print(f"Not handled properly: {self.type}")
    
    if 'embed' in reply:
      reply['embed'].set_author(
        name=self.get_client_alias(self.originator, client)
      )
    
    try:
      await self.originator.channel.send(**reply)
    except discord.errors.HTTPException as e:
      if e.code == 50035: # Message too long
        note = f"The response to `{username}`'s request was too large, "
        note += "so I've uploaded it as a file instead:"
        if content := reply.get('content', None):
          content = reply['embed'].fields[-1]
        try:
          extra = reply['embed'].fields[0]
        except KeyError:
          extra = ''
        
        with ResultFile(content, self.originator.author.name, extra) as rf:
          await msg.channel.send(content=note, file=rf)
      


