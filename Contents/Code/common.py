#from configuration import *
#from collections import deque
#import copy
import time
import sys

ExpandedSearchTimeFactor = 10
ExpandedSearchMaxResultsFactor = 10

TVFavesDictVersion = 1
nzbItemsDictVersion = 1
nzbConfigDictVersion = 1
nntpConfigDictVersion = 2
FSConfigDictVersion = 1
mediaItemsQueueVersion = ''
tvRageItemsDictVersion = 1
imdbItemsDictVersion = 1
nntpSettingDictVersion = 1

TVFavesDict = 'TVFavesDict' + '_v' + str(TVFavesDictVersion)
nzbItemsDict = 'nzbItemsDict' + '_v' + str(nzbItemsDictVersion)
nzbConfigDict = 'nzbConfigDict' + '_v' + str(nzbConfigDictVersion)
nntpConfigDict = 'nntpConfigDict' + '_v' + str(nntpConfigDictVersion)
FSConfigDict = 'FSConfigDict' + '_v' + str(FSConfigDictVersion)
tvRageItemsDict = 'tvRageItemsDict' + '_v' + str(tvRageItemsDictVersion)
imdbItemsDict = 'imdbItemsDict' + '_v' + str(imdbItemsDictVersion)
nntpSettingDict = 'nntpSettingDict' + '_v' + str(nntpSettingDictVersion)

PREFIX      = "/video/newzworthy"
routeBase   = PREFIX + '/'

MovieSearchDays_Default = "0" # 0 is a special case, and basically means no filter
TVSearchDays_Default = "0" # 0 is a special case, and basically means no filter

persistentQueuing  = True

CACHE_INTERVAL     = 0
TVRAGE_CACHE_TIME  = 0
IMDB_CACHE_TIME    = 30
NEWZBIN_NAMESPACE  = {"report":"http://www.newzbin.com/DTD/2007/feeds/report/"}
longCacheTime      = 600
loglevel           = int(Prefs['NWLogLevel'])
LOGLEVEL_WATCHER_TIMEOUT = 3

#For negative testing purposes only
test_article_failure = []
test_server_failure = ['news.giganews.com', 'ssl.astraweb.com']

############################################################################################################################
# loglevels:
# 1: Errors only
# 2: Info + Errors
# 3: Debug Level 1 + Info + Errors
# 4: ALL Debug + Info + Errors - THIS IS A LOT OF LOGS BEING CREATED.  USE WISELY
# 5: EVEN MORE DEBUG!! - All the recursive stuff you just should never ever want to see!
# 6: CRAZY LEVELS OF DEBUG!!!! - I had to invent this level because I found even more useless stuff to log!
# 7: STUPID SHIT BEING LOGGED!!! - Don't use this unless you hate your filesystem and performance!!!!
# 8: I shouldn't even tell you about this level, but it's nice to know how to see some of the HTTP/XML request/responses
# 9: Why do I even have this level?  There can't possibly be any value to anything logged at this level.  Or is there?
############################################################################################################################
class nntpException(Exception):
  def __init__(self, mesg, id):
    self.mesg = mesg
    self.id = id

class AppService(object):
  def __init__(self, app):
    funcName = "[common.AppService]"
    log(9, funcName, 'Received app:', str(app))
    self.app = app
    log(9, funcName, 'calling init()')
    self.init()
  
  def init(self):
    # Here to be overridden by instance implementations
    pass

class NWQueue(object):
  """Used to persist lists using Plex Framework's Data capability"""
  def __init__(self, name):
    funcName = '[NWQueue.__init__][' + name + ']'
    self.name = name
    self.dictName = ("NWQueue_" + name)
    self.queueDictName = self.dictName + '_queue'
    self.queue = []
    self.queueLock = Thread.Lock('queueLock')
    self.queueCopyLock = Thread.Lock('queueCopyLock')
    self.useLocking = True
    self.saveLocking = True
    self.lastSave = 0
    self.saveInterval = 0 #seconds
    self.copyBeforeSave = False
    
    if Data.Exists(self.queueDictName):
      try:
        log(5, funcName, self.queueDictName, 'found!')
        savedQueue = Data.LoadObject(self.queueDictName)
        log(7, funcName, 'Found:', savedQueue)
        self.queue.extend(savedQueue)
        log(5, funcName, self.queueDictName, 'length retrieved:',len(self.queue))
      except:
        log(5, funcName, self.dictName, 'error retrieving saved queue, recreating')
        log(7, funcName, self.dictName, Exception)
      finally:
        pass #self.save()
    else:
      log(5, funcName, self.queueDictName, 'not found, it will be created')

    self.save()
  ##end __init__
  def __repr__(self):
    return self.queue
  def __len__(self):
    return len(self.queue)
  def __iter__(self):
    return self.queue
  
  def reset(self):
    self.queue = []
    self.save()

  def append(self, item):
    #This function does nothing except pass the request to self.put, consolidating logic.
    #This interface is available for compatibility with list commands
    funcName = "[" + self.dictName + ".append]"
    self.put(item)
  def put(self, item):
    """Puts an item into this queue"""
    funcName = "[" + self.dictName + ".put]"
    log(7, funcName, 'Putting an item on the queue')
    resp = False
    try:
      if self.useLocking: Thread.AcquireLock(self.queueLock)
      self.queue.append(item)
      self.save()
      resp = True
    except:
      resp = False
    finally:
      if self.useLocking: Thread.ReleaseLock(self.queueLock)
    return resp
  def get(self):
    #This function essentially does nothing except pass the request down to the self.pop function.
    """Gets and removes an item from the queue, same as pop()"""
    funcName = "[" + self.dictName + ".get]"
    try:
      item = self.pop()
      return item
    except:
      log(1, funcName, 'Error getting item')
      raise
      return False
  def pop(self, position=0):
    """Gets and removes an item from the queue"""
    funcName = "[" + self.dictName + ".pop]"
    log(7, funcName, 'Getting an item from the queue')
    try:
      if self.useLocking: Thread.AcquireLock(self.queueLock)
      if position > 0:
        item=self.queue.pop()
      else:
        item=self.queue.pop(position)
      
      #log(7, funcName, 'Popped item:', item)
      self.save()
    except:
      log(1, funcName, 'Error popping item')
      raise
      item = False
    finally:
      if self.useLocking: Thread.ReleaseLock(self.queueLock)
      return item
  def remove(self, item):
    """Removes an item from the queue"""
    funcName = "[" + self.dictName + ".remove]"
    resp = False
    log(7, funcName, 'Removing an item')
    try:
      try:
        if self.useLocking: Thread.AcquireLock(self.queueLock)
        self.queue.remove(item)
      except:
        pass
      self.save()
      resp = True
    except:
      resp = False
    finally:
      if self.useLocking: Thread.ReleaseLock(self.queueLock)
    return resp
  def save(self):
    funcName = "[" + self.dictName + ".save]"
    log(6, funcName, 'Saving', self.dictName)
    lastStep = 'starting, checking last saved time'
    rightNow = time.time()
    if rightNow - self.lastSave > self.saveInterval:
      try:
        if self.saveLocking: Thread.AcquireLock(self.queueCopyLock)
        #Dict[self.queueDictName] = []
        
        log(7, funcName, 'Saving queue', self.dictName)
        if self.copyBeforeSave:
          log(7, funcName, 'Duplicating', self.dictName, 'queue')
          queueToSave = []
          lastStep = 'Duplicating ' + self.dictName + ' queue'
          queueToSave.extend(self.queue)
          lastStep = 'Saving ' + self.dictName + ' queue'
          Data.SaveObject(self.queueDictName, queueToSave)
          #Dict[self.queueDictName] = queueToSave
          log(7, funcName, 'Saved', self.queueDictName)#, 'queue:', len(Dict[self.queueDictName]))
        else:
          lastStep = "Saving queue"
          Data.SaveObject(self.queueDictName, self.queue)
          #Dict[self.queueDictName] = self.queue
          log(7, funcName, 'Saved', self.queueDictName)
      except:
        log(5, funcName, 'ERROR at step:', lastStep)
        raise
      finally:
        if self.saveLocking: Thread.ReleaseLock(self.queueCopyLock)
        log(7, funcName, 'Setting lastSave time')
        self.lastSave = time.time()

class NewzworthyApp(object):
  def __init__(self):
    funcName = "[common.NewzWorthyApp.__init__]"
    self.loglevel = int(Prefs['NWLogLevel'])
    Thread.Create(log_level_watcher)
    log(5, funcName, 'importing downloader')
    from downloader import Downloader
    log(5, funcName, 'importing Queue')
    from queue import Queue
    from unpacker import Unpacker, UnpackerManager
    from nntpclient import nntpManager
    from updater import Updater
    from migrator import Migrator
    from configuration import configuration

    try:
      self.num_client_threads = int(Dict[nntpSettingDict]['TotalConnections'])
    except:
      self.num_client_threads = 1
    log(4, funcName, 'Initializing Queue')
    self.queue = Queue(self)
    log(4, funcName, 'Initializing Downloader')
    self.cfg = configuration(self)
    self.nntpManager = nntpManager(self)
    self.recoverer = None
    self.stream_initiator = None
    self.updater = Updater()
    self.migrator = Migrator(self)
    self.downloader = Downloader(self)
    self.unpacker_manager = UnpackerManager(self)
    
class article(object):
  def __init__(self):
    self.newzbinID = ''
    self.mediaType = ''
    self.title = ''
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
    self.videoformat = []
    self.genre = []
    self.language = []
    self.audioformat = []
    self.videosource = ''
    self.groups = []
    self.subtitles = []
    
  @property
  def summary(self):
    return self.description
  @property
  def attributes_and_summary(self):
    summary = ''
    try:
      if self.videosource != '':
        summary = 'Video Source: ' + self.videosource
    except:
      pass
    try:
      if len(self.videoformat)>=1:
        if summary != '':
          summary += '\n'
        summary += 'Video Formats: ' + ', '.join(str(i) for i in self.videoformat)
    except:
      pass
    try:
      if len(self.audioformat)>=1:
        if summary != '':
          summary += '\n'
        summary += 'Audio Formats: ' + ', '.join(str(i) for i in self.audioformat)
    except:
      pass
    try:
      if len(self.language)>=1:
        if summary != '':
          summary += '\n'
        summary += 'Languages: ' + ', '.join(str(i) for i in self.language)
    except:
      pass
    try:
      if len(self.subtitles)>=1:
        if summary != '':
          summary += '\n'
        summary += 'Subtitles: ' + ', '.join(str(i) for i in self.subtitles)
    except:
      pass
    if summary != '':
      summary += '\n'
    summary += self.description
    return summary

class NZBService(object):
  def __init__(self):
    self.newzbinUsername=''
    self.newzbinPassword=''
    self.nzbmatrixUsername=''
    self.nzbmatrixPassword=''
    self.nzbmatrixAPIKey=''
    

####################################################################################################
# def loadQueueFromDisk(path):
#   funcName = "[loadQueueFromDisk]"
#   if Core.storage.dir_exists(Core.storage.join_path(Core.storage.data_path, path)):
#     basePath = Core.storage.join_path(Core.storage.data_path, path)
#     mediaDirs = Core.storage.list_dirs(basePath)
#     for item in mediaDirs:
#       if Core.storage.dir_exists(item):
#         log(6,funcName, 'found dir', item)

####################################################################################################

def log_level_watcher():
  Log.Info('log_level_watcher started')
  while True:
    try:
      global loglevel
      pref_log_level = int(Prefs['NWLogLevel'])
      #if app.loglevel != pref_log_level:
        #Log.Info('loglevel changed from ' + str(app.loglevel) + ' to ' + str(pref_log_level))
        #loglevel = int(pref_log_level)
      change_log_level(int(pref_log_level))
    except:
      Log.Critical('Unable to update loglevel')
      raise
    finally:
      time.sleep(LOGLEVEL_WATCHER_TIMEOUT)

def change_log_level(new_loglevel):
  global loglevel
  loglevel = int(new_loglevel)
  
def log(messageloglevel, *args):
  try:
    # Use the built-in logging, combined with log levels
    #loglevel = int(Prefs['NWLogLevel'])
    #loglevel = 7
    global loglevel
    if (loglevel>=messageloglevel):
      logmessage = "[Newzworthy Log][" + str(messageloglevel) + "/" + str(loglevel) + "] "# + message
      for arg in args:
        logmessage += " " + str(arg)
      Log(logmessage)
  except:
    ex, errmsg, tb = sys.exc_info()
    Log('Failed to log message, here''s why: ' + str(errmsg))
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
  value = value.replace(" ","_")
  value = value.replace('"','')
  value = value.replace("'","")
  value = value.replace("`","")
  value = value.replace(":","-")
  value = value.replace("&","_")
  value = value.replace("/", "_")
  value = value.replace("=","-")
  value = value.replace(",", "_")
  value = value.replace("\|", "_")
  value = value.replace("(", "_")
  value = value.replace(")", "_")
  value = value.replace('\\', "_")
  value = value.replace('?', '_')
  value = value.replace(';', '_')
  value = value.replace('<', '_')
  value = value.replace('>', '_')
  value = value.replace('*', '_')
  value = value.replace('@', '_')
  value = value.replace('%', '')
  value = value.replace('!', '')
  value = value.replace('#', '_')
  value = value.replace('^', '_')
  value = value.replace("[", "_")
  value = value.replace("]", '_')
  value = value.replace("{", '_')
  value = value.replace("}", '_')
  value = value.replace("~", '_')
  value = value.replace("#", '_')
  value = value.replace("~", "_")
  value = value.encode('ascii', 'ignore')
  return value
  
####################################################################################################
@route(routeBase + 'StupidUselessFunction/{key}')
def StupidUselessFunction(key, sender='nothing'):
  # A noop function, just for creating "blank" context menus
  return True

####################################################################################################
def convert_bytes(bytes):
  bytes = float(bytes)
  if bytes >= 1099511627776:
    terabytes = bytes / 1099511627776
    size = '%.2fT' % terabytes
  elif bytes >= 1073741824:
    gigabytes = bytes / 1073741824
    size = '%.2fG' % gigabytes
  elif bytes >= 1048576:
    megabytes = bytes / 1048576
    size = '%.2fM' % megabytes
  elif bytes >= 1024:
    kilobytes = bytes / 1024
    size = '%.2fK' % kilobytes
  else:
    size = '%.2fb' % bytes
  return size


####################################################################################################
# def bool(value):
#   try:
#     if value=="true": return True
#     if value=="false": return False
#     if value=="1": return True
#     if value=="0": return False
#     if len(value) < 1: return False
#     if value==None: return False
#     if value.count < 1: return False
#     if value==True: return True
#     if value==False: return False
#   except:
#     return True