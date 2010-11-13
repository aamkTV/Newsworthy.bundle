from report import Report
from unpacker import Unpacker
from nzbf import NZB
from Recoverer import Recoverer
import time
#from common import AppService

media_extensions = ['avi', 'mkv', 'mov', 'wmv', 'mp4', 'm4v']
app = None

class MediaItem(object):
  global app
  def __init__(self, nzbID, report, nzb_xml):
#  def __init__(self, queue, nzbID, report, nzb_xml):
    funcName = "[queue.MediaItem.__init__]"
    #self.queue = queue
    self.id = nzbID
    self.report = report
    self.nzb = NZB(nzb_xml)
    self.valid = True
    self.failed_articles = []

    log(4, funcName, 'Setting media path to', Core.storage.data_path, '/Media')
    self.media_path = Core.storage.join_path(Core.storage.data_path, 'Media')
    log(4, funcName, 'Making sure', self.media_path, 'exists')
    Core.storage.make_dirs(self.media_path)


    log(5, funcName, "making", self.incoming_path)
    Core.storage.make_dirs(self.incoming_path)
    log(5, funcName, "making", self.completed_path)
    Core.storage.make_dirs(self.completed_path)
    
    self.files = None
    self.stream_initiator = None
    
    self.recoverable = False
    self.recovery_complete = False
    self.repair_percent = 0
    self.recovery_files_added = False
    
    self.downloading = False
    self.complete = False
    self.downloadComplete = False
    
    self.download_start_time = None
    
    self.incoming_files = []
    
    nzb_path = self.path(cleanFSName(self.report.title) + '.nzb')
    if not Core.storage.file_exists(nzb_path):
      Core.storage.save(nzb_path, XML.StringFromElement(nzb_xml))
  
  @property
  def recovered(self):
    try:
      if self.recoverable and self.recovery_complete:
        return True
      else:
        return False
    except:
      return True
      
  @property
  def failing(self):
    try:
      if len(self.failed_articles) > 0:
        return True
      else:
        return False
    except:
      return False

  def add_failed_article(self, article_id):
    self.failed_articles.append(article_id)
    if not self.recovery_files_added:
      self.recovery_files_added = True
      self.add_pars_to_download()
      self.save()

  def delete(self):
    funcName = '[Queue.MediaItem.delete]'
    self.valid = False
    try:
      up = app.unpacker_manager.get_unpacker(self)
      if up: app.unpacker_manager.end_unpacker(self)
      if app.recoverer:
        if app.recoverer.item.id == self.id:
          app.recoverer.stopped = True
          app.recoverer = None
    except:
      log(6, funcName, 'Unable to stop unpacker or recoverer')

    myPath = Core.storage.join_path(self.media_path, str(self.report.mediaType), cleanFSName(self.report.title))
    Core.storage.remove_tree(myPath)
    return True
      
  def path(self, subdir):
    funcName = "[queue.MediaItem.path]"
    #log(5, funcName, 'returning this folder:', self.media_path, self.id, subdir)
    path = Core.storage.join_path(self.media_path, str(self.report.mediaType), cleanFSName(self.report.title), subdir)
    log(8, funcName, 'requested path type:', subdir, ': path:',path)
    return path
    
  @property
  def incoming_path(self):
    return self.path('Incoming')
  
  @property
  def completed_path(self):
    return self.path('Completed')
    
  @property
  def play_ready(self):
    funcName = '[Queue.MediaItem.play_ready]'
    ready = False
    if app.unpacker_manager.get_unpacker(self):
      if app.unpacker_manager.get_unpacker(self).play_ready:
        log(7, funcName, 'app.unpacker.play_ready')
        if self.fullPathToMediaFile:
          log(7, funcName, 'self.fullPathToMediaFile:',self.fullPathToMediaFile)
          ready = True
        else:
          log(7, funcName, 'No media file found')
      else:
        log(7, funcName, 'NOT app.unpacker_manager.get_unpacker(self).play_ready')
    else:
      log(7, funcName, 'app.unpacker_manager.get_unpacker(self) == False')
    if self.complete and self.fullPathToMediaFile:
      ready = True
    log(7, funcName, 'Returning:', ready)
    return ready
    
  @property
  def play_ready_percent(self):
    if self.play_ready:
      return 100
    else:
      return self.nzb.rars[0].percent_done
  
  @property
  def total_bytes(self):
    return self.nzb.total_bytes
  
  @property
  def downloaded_bytes(self):
    return self.nzb.downloaded_bytes()
  
  @property
  def percent_complete(self):
    return ((float(self.downloaded_bytes)/float(self.total_bytes))*100)
    
  @property
  def speed(self):
    funcName = '[Queue.MediaItem.speed]'
    delta = Datetime.Now() - self.download_start_time
    log(7, funcName, 'delta:', delta)
    try:
      log(7, funcName, 'downloaded_bytes:', self.downloaded_bytes, "delta.seconds:", delta.seconds)
      bps = float(self.downloaded_bytes) / float(delta.seconds)
    except:
      log(3, funcName, 'Error calculating download speed')
      bps = 1
    return bps
  
  @property
  def secs_left(self):
    remaining = self.total_bytes - self.downloaded_bytes
    try:
      seconds_left = int(float(remaining) / self.speed)
    except:
      seconds_left = False
    return seconds_left

  @property
  def play_ready_time(self):
    funcName = "[Queue.MediaItem.play_ready_time]"
    if not self.download_start_time:
      log(7, funcName, 'self.download_start_time not set')
      return
    
    rar = self.nzb.rars[0]
    total = rar.total_bytes
    done = rar.downloaded_bytes
    remaining = total - done
    delta = Datetime.Now() - self.download_start_time
    try:
      secs_left = int(float(remaining) / self.speed)
    except:
      secs_left = 999999
    log(7, funcName, 'seconds left:', secs_left)
    return secs_left
  
  @property
  def download_time_remaining(self):
    if not self.download_start_time:
      return
    remaining = self.total_bytes - self.downloaded_bytes
    delta = Datetime.Now() - self.download_start_time
    try:
      secs_left = int(float(remaining) / self.speed)
    except:
      secs_left = 999999
    return secs_left
  
  @property
  def fullPathToMediaFile(self):
    funcName = '[Queue.MediaItem.fullPathToMediaFile]'
    fullPath = False
    log(8, funcName, self.files)
    for name in self.files:
      index = name.rfind('.')
      if index > -1:
        ext = name[index+1:]
        if ext in media_extensions:
          log(8, funcName, 'Found this file, returning full path:', Core.storage.join_path(self.completed_path, name))
          fullPath = Core.storage.join_path(self.completed_path, name)
          break
    else:
      log(5, funcName, 'Could not find a media file')
    log(8, funcName, 'Returning:', fullPath)
    return fullPath
  
  @property
  def mediaFileName(self):
    funcName = '[Queue.MediaItem.mediaFileName]'
    MFName = False
    for name in self.files:
      index = name.rfind('.')
      if index > -1:
        ext = name[index+1:]
        if ext in media_extensions:
          log(7, funcName, 'Found this file, returning full path:', Core.storage.join_path(self.completed_path, name))
          MFName = name
          break
    else:
      log(5, funcName, 'Could not find a media file')
    return MFName

  @property
  def stream(self):
    funcName = "[queue.MediaItem.stream]"
    global app
    
    # Reset, but do not cross the streams.
    # What happens if we cross the streams?  Very bad things, Ray.
    if not app.stream_initiator == None:
      log(6, funcName, 'Resetting the stream_initiator')
      app.stream_initiator = None
    
    if not app.stream_initiator and self.play_ready and self.files:
      log(7, funcName, "Files:", self.files)
      mediaFile = self.fullPathToMediaFile
      if self.complete:
        filesize = None
      else:
        filesize = self.files[self.mediaFileName]
        #filesize = None
      log(6, funcName, "initiating Stream.LocalFile with mediaFile:", mediaFile, "and moredata:", (not self.complete), "and size:", filesize)
      app.stream_initiator = Stream.LocalFile(
	    mediaFile,
	    size = filesize
      )
      log (6, funcName, "initiated stream")
    log(6, funcName, "returning stream_initiator:", app.stream_initiator)
    return app.stream_initiator
  
  def fileCompleted(self, filename):
    funcName = "[queue.MediaItem.fileCompleted]"
    fileExists = False
    try:
      fileExists = Core.storage.file_exists(Core.storage.join_path(self.incoming_path, filename))
      if fileExists:
        log(7, funcName, "Found file:", filename)
      else:
        log(7, funcName, "File not found:", filename)
    except:
      log(2, funcName, "Error when looking for file:", filename)
    return fileExists

  def add_incoming_file(self, filename):
    funcName = "[Queue.MediaItem.add_incoming_file]"
    if self.valid:
      #cleanFilename = cleanFSName(filename)
      self.incoming_files.append(filename)
      #Core.storage.save(Core.storage.join_path(self.incoming_path, filename), data)
      #log(6, funcName,"Saved incoming data file", filename, "for item with id", self.id)
      if not self.failing:
        self.unpack(filename)
      elif self.failing:
        if len(self.incoming_files) == len(self.nzb.rars):
          log(6, funcName, 'Downloaded final par file:', filename)
          self.recover_par()
      self.save()
    else:
      log(7, funcName, 'No need to save, this file is being deleted')

  def unpack(self, filename):
    funcName = "[Queue.MediaItem.unpack]"
    global app
    up = app.unpacker_manager.get_unpacker(self)
    if not up:
      log(6, funcName, 'Unpacker does not exist, creating one')
      up = app.unpacker_manager.new_unpacker(self)
      log(7, funcName, 'Getting contents of unpacker')
      self.files = up.get_contents()
      log(7, funcName, 'Contents of unpacker:', self.files)
      if filename != self.nzb.rars[0].name:
        log(7, funcName, 'filename is not the first rar in the list')
        up.add_part(self.nzb.rars[0].name)
        up.add_part(filename)
      log(7, funcName, 'starting unpacker')
      up.start()
      log(7, funcName, 'unpacker started')
    else:
      log(6, funcName, 'Adding file to existing unpacker')
      up.add_part(filename)
  
  def finished_unpacking(self):
    funcName = "[Queue.MediaItem.finished_unpacking]"
    if self.failing and not self.recovered:
      # Get the recovery process kicked off
      self.recover_par()
    else:
      log(6, funcName, 'Setting item complete to true for id:', self.id)
      self.complete = True
      app.unpacker_manager.end_unpacker(self)
      log(5, funcName, "Finished unpacking item with id", self.id, "removing incoming data files")    
      Core.storage.remove_tree(Core.storage.join_path(self.incoming_path))
    self.save()
  
  def add_pars_to_download(self):
    funcName = '[Queue.MediaItem.add_pars_to_download]'
    self.nzb.rars.extend(Util.ListSortedByAttr(self.nzb.pars, 'name'))
    app.downloader.add_files_to_download(self.nzb.pars, self)
    self.save()
    log(3, funcName, 'Added pars to download:', Util.ListSortedByAttr(self.nzb.pars, 'name'))
    
  def recover_par(self):
    funcName = '[Queue.MediaItem.recover_par]'
    log(3, funcName, 'Starting recover')
    app.recoverer = Recoverer(app, self)
    app.recoverer.start()
    Thread.Create(self.recovery_monitor)
    
  def recovery_monitor(self):
    funcName = '[Queue.MediaItem.recovery_monitor]'
    r = app.recoverer
    while True:
      if r.recoverable:
        self.recoverable = True
        self.repair_percent = r.repair_percent
        self.save()
      else:
        if r.recovery_complete:
          self.recoverable = False
          self.recovery_complete = True
          self.save()
          break
          
      # When repairs are completed, unpack and call it a day
      if self.recoverable and r.recovery_complete:
        log(3, funcName, 'Recovery complete, unpacking, saving, and exiting')
        self.unpack(self.nzb.rars[0].name)
        self.recovery_complete = True
        self.failed_articles = []
        self.save()
        break
      else:
        log(4, funcName, 'Waiting for recovery to complete, current status:', r.repair_percent)
        time.sleep(5)
        
  def save(self):
    funcName = "[Queue.MediaItem.save]"
    log(6, funcName, 'Saving item in the queue')
    if persistentQueuing:
      if app.queue.getItem(self.id):
        app.queue.items.save()

####################################################################################    
class Queue(AppService):
  def init(self):
    funcName = "[Queue.init]"
#     log(4, funcName, 'Setting media path to', Core.storage.data_path, '/Media')
#     self.media_path = Core.storage.join_path(Core.storage.data_path, 'Media')
#     log(4, funcName, 'Making sure', self.media_path, 'exists')
#     Core.storage.make_dirs(self.media_path)
    log(4, funcName, 'Initializing items')
    self.items = self.setupItemQueue()
    global app
    app = self.app
    
  def setupItemQueue(self, reset=False):
    funcName = '[Queue.Queue.setupItemQueue]'
    if persistentQueuing:
      self.items = NWQueue('mediaItems' + mediaItemsQueueVersion)
    else:
      items = []
    return self.items
  
  def resetItemQueue(self):
    if persistentQueuing:
      self.items.reset()
    else:
      self.items = []
      
  def getItem(self, id):
    funcName = "[Queue.getItem]"
    theItem = None
    if not id:
      return False    
    for item in self.items:
      itemID = item.id
      if item.id == id:
        theItem = item
        break
    if theItem == None: return False
    return theItem
  
  @property
  def downloadingItems(self):
    downloadList = []
    for item in self.items:
      try:
        if (not item.downloadComplete) and item.downloading:
          downloadList.append(item)
      except:
          pass
    return downloadList
    
  @property
  def downloadQueue(self):
    downloadList = []
    for item in self.items:
      try:
        if (not item.downloadComplete) and (not item.downloading):
          downloadList.append(item)
      except:
        pass
    return downloadList
  
  @property
  def downloadableItems(self):
    downloadList = []
    downloadList.extend(self.downloadingItems)
    downloadList.extend(self.downloadQueue)
    return downloadList

  @property
  def completedItems(self):
    downloadList = []
    for item in self.items:
      try:
        if item.complete or item.downloadComplete:
          downloadList.append(item)
      except:
        pass
    return downloadList
    
  def add(self, nzbID, nzbService, article):
    """Gets the NZB file's URL, gets the report information, creates a MediaItem object, and puts it on the items queue"""
    funcName = "[Queue.add]"
    #report_el = nzbService.report(report_id)
    log(4, funcName, 'Received ID:', nzbID, 'NZBService:', nzbService)
    log(4, funcName, 'Getting NZB XML for', article.title)
    nzb_xml = XML.ElementFromURL(nzbService.downloadNZBUrl(nzbID))
    #log(7, funcName, 'Got this xml:', XML.StringFromElement(nzb_xml))
    item = MediaItem(nzbID, article, nzb_xml)
#    item = MediaItem(self, nzbID, article, nzb_xml)
    log(5, funcName, 'Adding this to the queue.  Items in queue:', len(self.items))
    self.items.append(item)
    #log(5, funcName, 'Item added to queue.  Items in queue:', len(self.items))
    #item.download()
    return item