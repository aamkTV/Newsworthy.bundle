#from configuration import *
from collections import deque

class AppService(object):
  def __init__(self, app):
    funcName = "[common.AppService]"
    log(4, funcName, 'Received app:', str(app))
    self.app = app
    log(5, funcName, 'calling init()')
    self.init()
  
  def init(self):
    # Here to be overridden by instance implementations
    pass

class NWQueue(deque):
  def __init__(self, name):
    funcName = "[NWQueue.__init__]"
    self.queue = deque()
    self.name = name
    self.dictName = ("NWQueue_" + name)
    
    if self.dictName in Dict:
      log(5, funcName, self.dictName, 'found!')
      self.queue = Dict[self.dictName]
      log(5, funcName, self.dictName, 'length saved:',len(self.queue))
    else:
      log(5, funcName, self.dictName, 'not found, creating')
      Dict[self.dictName] = self.queue
  
  def __repr__(self):
    return self.queue

  def put(self, item):
    """Puts an item into this queue"""
    try:
      self.queue.append(item)
      #Save the queue to the Dict for persistence
      #try:
      Dict[self.dictName] = self.queue
      #except:
      #  pass
      return True
    except:
      return False
  def get(self):
    """Gets an item from the queue, and doesn't remove it from the queue"""
    try:
      item=self.queue[0]
      return item
    except:
      return False
  def pop(self):
    """Gets and removes an item from the queue"""
    try:
      item=self.popleft()
      Dict[self.dictName] = self.queue
      return item
    except:
      return False
  def remove(self, item):
    """Removes an item from the queue"""
    try:
      self.queue.remove(item)
      return True
    except:
      return False

class NewzworthyApp(object):
  def __init__(self):
    funcName = "[common.NewzWorthyApp.__init__]"
    log(5, funcName, 'importing downloader')
    from downloader import Downloader
    log(5, funcName, 'importing Queue')
    from queue import Queue
    #from service import Service

    try:
      self.num_client_threads = int(Dict[nntpConfigDict]['nntpConnections'])
    except:
      self.num_client_threads = 1
    log(4, funcName, 'Initializing Downloader')
    self.downloader = Downloader(self)
    log(4, funcName, 'Initializing Queue')
    self.queue = Queue(self)
    #self.service = Service(self)

class article(object):
  def __init__(self):
    self.newzbinID = ''
    self.mediaType = ''
    self.title = ''
    self.summary = ''
    self.duration = ''
    self.thumb = ''
    self.rating = ''
    self.fanart = ''
    self.size = ''
    self.reportAge = ''
    self.size = ''
    self.nzbID = ''
    self.moreInfoURL = ''
    self.moreInfo = ''
    self.sizeMB = ''
    self.description = ''
    self.subtitle = ''    

class NZBService(object):
  def __init__(self):
    self.newzbinUsername=''
    self.newzbinPassword=''
    self.nzbmatrixUsername=''
    self.nzbmatrixPassword=''
    self.nzbmatrixAPIKey=''
    
ExpandedSearchTimeFactor = 10
ExpandedSearchMaxResultsFactor = 10
TVFavesDict = 'TVFavesDict'
nzbItemsDict = 'nzbItemsDict'
nzbConfigDict = 'nzbConfigDict'
nntpConfigDict = 'nntpConfigDict'
FSConfigDict = 'FSConfigDict'

MovieSearchDays_Default = "0" # 0 is a special case, and basically means no filter
TVSearchDays_Default = "0" # 0 is a special case, and basically means no filter

CACHE_INTERVAL     = 0
TVRAGE_CACHE_TIME  = 0
IMDB_CACHE_TIME    = 30
NEWZBIN_NAMESPACE  = {"report":"http://www.newzbin.com/DTD/2007/feeds/report/"}
longCacheTime      = 600
loglevel=5

####################################################################################################
# loglevels:
# 1: Errors only
# 2: Info + Errors
# 3: Debug Level 1 + Info + Errors
# 4: ALL Debug + Info + Errors - THIS IS A LOT OF LOGS BEING CREATED.  USE WISELY
# 5: EVEN MORE DEBUG!! -- All the recursive stuff you just should never ever want to see!
####################################################################################################

####################################################################################################
def log(messageloglevel, *args):
  # Use the built-in logging, combined with log levels
  if (loglevel>=messageloglevel):
    logmessage = "[Newzworthy Log] "# + message
    for arg in args:
      logmessage += " " + str(arg)
    Log(logmessage)
  return True

####################################################################################################
def encodeText(value):
  # Please keep this updated.  If it weren't so expensive, I'd make this a webservice
  # It scares me to think this will be out of date someday
  value = value.replace("%", "%25")
  value = value.replace("+", "%2B")
  value = value.replace(" ", "+")
  value = value.replace("&", "%26")
  value = value.replace("#", "%23")
  value = value.replace("?", "%3F")
  value = value.replace("/", "%2F")
  value = value.replace("$", "%24")
  value = value.replace(",", "%2C")
  value = value.replace(":", "%3A")
  value = value.replace(";", "%3B")
  value = value.replace("=", "%3D")
  value = value.replace("@", "%40")
  value = value.replace("\"", "%22")
  value = value.replace("<", "%3C")
  value = value.replace(">", "%3E")
  
  return value

####################################################################################################
def cleanFSName(value):
  value = value.replace(" ","")
  value = value.replace('"','')
  value = value.replace("'","")
  value = value.replace("`","")
  value = value.replace(":","-")
  value = value.replace("&","-")
  value = value.replace("/", "-")
  value = value.replace("=","-")
  value = value.encode('ascii', 'ignore')
  return value
  
####################################################################################################
def StupidUselessFunction(key, sender='nothing'):
  # A noop function, just for creating "blank" context menus
  pass

####################################################################################################
def bool(value):
  try:
    if value=="true": return True
    if value=="false": return False
    if value=="1": return True
    if value=="0": return False
    if len(value) < 1: return False
    if value==None: return False
    if value.count < 1: return False
    if value==True: return True
    if value==False: return False
  except:
    return True