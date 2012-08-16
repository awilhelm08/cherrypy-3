#!/usr/bin/env python
import cherrypy, time, transaction
from persistent import Persistent
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList
# Set up template engine
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'))
# Set up db
from ZODB import FileStorage, DB
storage = FileStorage.FileStorage('test.fs')
db = DB(storage)
conn = db.open()
root = conn.root()

class User(Persistent):
  def __init__(self, name="", createDate=time.time(), owed=0, paid=0):
    self.name = name
    self.createDate = createDate
    self.owed = owed
    self.paid = paid
    self.balance = paid-owed

  def pay(self, amount):
    self.paid += int(amount)
    self.balance = self.paid-self.owed

  def getName(self):
    return self.name

class Expense(Persistent):
  def __init__(self, name="", paidby=User(), date=time.time(), cost=0):
    self.name = name
    self.paidby = paidby
    self.date = date
    self.cost = cost
    
class Root(object):
  @cherrypy.expose
  def index(self):
    # Sets up empty database
    if 'users' not in root:
      root['users'] = PersistentMapping()
      transaction.commit()
    if 'expenses' not in root:
      root['expenses'] = PersistentList()
      transaction.commit()
    tmpl = env.get_template('index.html')
    return tmpl.render(expenses=root['expenses'], users=root['users'].values())

  @cherrypy.expose
  def adduser(self, name=None):
    added = False
    if name != None:
      if name not in root['users']:
        root['users'][name] = User(name)
        root._p_changed = True
        transaction.commit()
        added = True
    tmpl = env.get_template('adduser.html')
    return tmpl.render(added=added)

  @cherrypy.expose
  def addexpense(self, name=None, amount=None, paidby=None):
    added = False
    if name != None and amount != None and paidby != None:
      root['expenses'].append(Expense(name, root['users'][paidby], time.time(), amount))
      root['users'][paidby].pay(amount)
      root._p_changed = True
      transaction.commit()
      added = True
    tmpl = env.get_template('addexpense.html')
    return tmpl.render(users=root['users'].values(), added=added)

cherrypy.quickstart(Root(), config={'global': {'server.socket_host':'0.0.0.0'},'/':{'tools.staticdir.root':'/home/ssmy/code/cherrypy/static'},'/css':{'tools.staticdir.on':True,'tools.staticdir.dir':'css'}})
