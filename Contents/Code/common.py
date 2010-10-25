#from configuration import *
#from collections import deque
#import copy
import time

ExpandedSearchTimeFactor = 10
ExpandedSearchMaxResultsFactor = 10

TVFavesDictVersion = 1
nzbItemsDictVersion = 1
nzbConfigDictVersion = 1
nntpConfigDictVersion = 1
FSConfigDictVersion = 1

TVFavesDict = 'TVFavesDict' + '_v' + str(TVFavesDictVersion)
nzbItemsDict = 'nzbItemsDict' + '_v' + str(nzbItemsDictVersion)
nzbConfigDict = 'nzbConfigDict' + '_v' + str(nzbConfigDictVersion)
nntpConfigDict = 'nntpConfigDict' + '_v' + str(nntpConfigDictVersion)
FSConfigDict = 'FSConfigDict' + '_v' + str(FSConfigDictVersion)
routeBase = '/video/newzworthy/'

MovieSearchDays_Default = "0" # 0 is a special case, and basically means no filter
TVSearchDays_Default = "0" # 0 is a special case, and basically means no filter

persistentQueuing  = True

CACHE_INTERVAL     = 0
TVRAGE_CACHE_TIME  = 0
IMDB_CACHE_TIME    = 30
NEWZBIN_NAMESPACE  = {"report":"http://www.newzbin.com/DTD/2007/feeds/report/"}
longCacheTime      = 600
loglevel           = 6

####################################################################################################
# loglevels:
# 1: Errors only
# 2: Info + Errors
# 3: Debug Level 1 + Info + Errors
# 4: ALL Debug + Info + Errors - THIS IS A LOT OF LOGS BEING CREATED.  USE WISELY
# 5: EVEN MORE DEBUG!! - All the recursive stuff you just should never ever want to see!
# 6: CRAZY LEVELS OF DEBUG!!!! - I had to invent this level because I found even more useless stuff to log!
# 7: STUPID SHIT BEING LOGGED!!! - Don't use this unless you hate your filesystem and performance!!!!
# 8: I shouldn't even tell you about this level, but it's nice to know how to see all the HTTP/XML request/responses
####################################################################################################

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

class NWQueue(object):
  """Used to persist lists using Plex Framework's Dict capability"""
  def __init__(self, name):
    funcName = '[NWQueue.__init__][' + name + ']'
    self.name = name
    self.dictName = ("NWQueue_" + name)
    self.queueDictName = self.dictName + '_queue'
    self.dequeuedDictName = self.dictName + '_dequeued'
    self.queue = []
    self.dequeued = []
    self.queueLock = Thread.Lock('queueLock')
    self.dequeuedLock = Thread.Lock('dequeuedLock')
    self.queueCopyLock = Thread.Lock('queueCopyLock')
    self.dequeuedCopyLock = Thread.Lock('dequeuedCopyLock')
    self.useLocking = True
    self.saveLocking = True
    self.lastSave = 0
    self.saveInterval = 0 #seconds
    self.copyBeforeSave = False
    
    if self.queueDictName in Dict:
      try:
        log(5, funcName, self.queueDictName, 'found!')
        savedQueue = Dict[self.queueDictName]
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
      #self.save()

    if self.dequeuedDictName in Dict:
      try:
        log(5, funcName, self.dequeuedDictName, 'found!')
        savedQueue = Dict[self.dequeuedDictName]
        log(7, funcName, 'Found:', savedQueue)
        self.dequeued.extend(savedQueue)
        log(5, funcName, self.dequeuedDictName, 'length retrieved:',len(self.dequeued))
      except:
        log(5, funcName, self.dictName, 'error retrieving saved dequeued, recreating')
        log(7, funcName, self.dictName, Exception)
      finally:
        pass #self.save()
    else:
      log(5, funcName, self.dequeuedDictName, 'not found, it will be created')
      #self.save()
    self.save()
  ##end __init__
  def __repr__(self):
    return self.queue
  def __len__(self):
    return len(self.queue)
    #return self.queue.qsize()
  def __iter__(self):
    return self.queue
  
  def reset(self):
    self.queue = []
    self.dequeued = []
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
      if self.useLocking: Thread.AcquireLock(self.dequeuedLock)
      if position > 0:
        item=self.queue.pop()
      else:
        item=self.queue.pop(position)
      
      #log(7, funcName, 'Popped item:', item)
      self.dequeued.append(item)
      self.save()
    except:
      log(1, funcName, 'Error popping item')
      raise
      item = False
    finally:
      if self.useLocking: Thread.ReleaseLock(self.dequeuedLock)
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
      try:
        if self.useLocking: Thread.AcquireLock(self.dequeuedLock)
        self.dequeued.remove(item)
      except:
        pass
      self.save()
      resp = True
    except:
      resp = False
    finally:
      if self.useLocking: Thread.ReleaseLock(self.queueLock)
      if self.useLocking: Thread.ReleaseLock(self.dequeuedLock)
    return resp
  def save(self):
    funcName = "[" + self.dictName + ".save]"
    log(6, funcName, 'Saving', self.dictName)
    lastStep = 'starting, checking last saved time'
    rightNow = time.time()
    if rightNow - self.lastSave > self.saveInterval:
      try:
        if self.saveLocking: Thread.AcquireLock(self.queueCopyLock)
        if self.saveLocking: Thread.AcquireLock(self.dequeuedCopyLock)
        Dict[self.queueDictName] = []
        Dict[self.dequeuedDictName] = []
        
        log(7, funcName, 'Saving queue', self.dictName)
        if self.copyBeforeSave:
          log(7, funcName, 'Duplicating', self.dictName, 'queue')
          queueToSave = []
          lastStep = 'Duplicating ' + self.dictName + ' queue'
          queueToSave.extend(self.queue)
          lastStep = 'Saving ' + self.dictName + ' queue'
          Dict[self.queueDictName] = queueToSave
          log(7, funcName, 'Saved', self.dictName, 'queue:', len(Dict[self.queueDictName]))
        else:
          lastStep = "Saving queue"
          Dict[self.queueDictName] = self.queue
          
        log(7, funcName, 'Saving dequeue', self.dictName) 
        if self.copyBeforeSave:
          log(7, funcName, 'Duplicating', self.dictName, 'dequeued')
          dequeuedToSave = []
          lastStep = 'Duplicating ' + self.dictName + 'dequeued'
          dequeuedToSave.extend(self.dequeued)
          lastStep = 'Saving ' + self.dictName + ' dequeued'
          Dict[self.dequeuedDictName] = dequeuedToSave
          log(7, funcName, 'Saved', self.dictName, 'dequeued:', len(Dict[self.dequeuedDictName]))
        else:
          lastStep = "Saving dequeue"
          Dict[self.dequeuedDictName] = self.dequeued
      except:
        log(5, funcName, 'ERROR at step:', lastStep)
        raise
      finally:
        if self.saveLocking: Thread.ReleaseLock(self.queueCopyLock)
        if self.saveLocking: Thread.ReleaseLock(self.dequeuedCopyLock)
        log(7, funcName, 'Setting lastSave time')
        self.lastSave = time.time()


class NewzworthyApp(object):
  def __init__(self):
    funcName = "[common.NewzWorthyApp.__init__]"
    log(5, funcName, 'importing downloader')
    from downloader import Downloader
    log(5, funcName, 'importing Queue')
    from queue import Queue
    from unpacker import Unpacker
    from nntpclient import nntpManager
    from updater import Updater

    try:
      self.num_client_threads = int(Dict[nntpConfigDict]['nntpConnections'])
    except:
      self.num_client_threads = 1
    log(4, funcName, 'Initializing Queue')
    self.queue = Queue(self)
    log(4, funcName, 'Initializing Downloader')
    self.downloader = Downloader(self)
    self.unpacker = None
    self.stream_initiator = None
    self.nntpManager = nntpManager(self)
    self.updater = Updater()
    #self.service = Service(self)

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
    if self.videosource != '':
      summary = 'Video Source: ' + self.videosource
    if len(self.videoformat)>=1:
      if summary != '':
        summary += '\n'
      summary += 'Video Formats: ' + ', '.join(str(i) for i in self.videoformat)
    if len(self.audioformat)>=1:
      if summary != '':
        summary += '\n'
      summary += 'Audio Formats: ' + ', '.join(str(i) for i in self.audioformat)
    if len(self.language)>=1:
      if summary != '':
        summary += '\n'
      summary += 'Languages: ' + ', '.join(str(i) for i in self.language)
    if len(self.subtitles)>=1:
      if summary != '':
        summary += '\n'
      summary += 'Subtitles: ' + ', '.join(str(i) for i in self.subtitles)
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