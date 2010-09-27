from report import Report
from unpacker import Unpacker
from nzbf import NZB
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

    log(4, funcName, 'Setting media path to', Core.storage.data_path, '/Media')
    self.media_path = Core.storage.join_path(Core.storage.data_path, 'Media')
    log(4, funcName, 'Making sure', self.media_path, 'exists')
    Core.storage.make_dirs(self.media_path)


    log(5, funcName, "making", self.incoming_path)
    Core.storage.make_dirs(self.incoming_path)
    log(5, funcName, "making", self.completed_path)
    Core.storage.make_dirs(self.completed_path)
    
    self.unpacker = None
    self.files = None
    self.stream_initiator = None
    
    self.downloading = False
    self.complete = False
    self.downloadComplete = False
    
    self.download_start_time = None
    
    self.incoming_files = []
    
    #report_path = self.path('ReportData')
    nzb_path = self.path('SourceData')
    if not Core.storage.file_exists(nzb_path):
      Core.storage.save(nzb_path, XML.StringFromElement(nzb_xml))
    #if not Core.storage.file_exists(report_path):
    #  Core.storage.save(report_path, XML.StringFromElement(report_el))
  
  def delete(self):
    funcName = '[Queue.MediaItem.delete]'
    try:
      if app.unpacker:
        log(7, funcName, 'checking if existing unpacker is for this item')
        if app.unpacker.item.id == self.id:
          log(7, funcName, 'stopping unpacker for this item')
          app.unpacker.stopped = True
          #app.unpacker = None
    except:
      log(6, funcName, 'Unable to stop unpacker')

    myPath = Core.storage.join_path(self.media_path, cleanFSName(self.report.title))
    Core.storage.remove_tree(myPath)
    return True
      
  def path(self, subdir):
    funcName = "[queue.MediaItem.path]"
    #log(5, funcName, 'returning this folder:', self.media_path, self.id, subdir)
    path = Core.storage.join_path(self.media_path, cleanFSName(self.report.title), subdir)
    log(7, funcName, 'requested path type:', subdir, ': path:',path)
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
    if app.unpacker != None:
      log(7, funcName, 'app.unpacker != None')
      if app.unpacker.item.id == self.id:
        log(7, funcName, 'app.unpacker.item.id (' + app.unpacker.item.id + ') == self.id (' + self.id + ')')
        if app.unpacker.play_ready:
          log(7, funcName, 'app.unpacker.play_ready')
          if self.fullPathToMediaFile:
            log(7, funcName, 'self.fullPathToMediaFile:',self.fullPathToMediaFile)
            ready = True
          else:
            log(7, funcName, 'No media file found')
        else:
          log(7, funcName, 'NOT app.unpacker.play_ready')
      else:
        log(7, funcName, 'app.unpacker.item.id (' + app.unpacker.item.id + ') != self.id (' + self.id + ')')
    else:
      log(7, funcName, 'app.unpacker == None')
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
    rar = self.nzb.rars[0]
    return rar.total_bytes
  
  @property
  def downloaded_bytes(self):
    rar = self.nzb.rars[0]
    return rar.downloaded_bytes
  
  @property
  def speed(self):
    delta = Datetime.Now() - self.download_start_time
    try:
      bps = float(self.downloaded_bytes) - float(delta.seconds)
    except:
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
    
#    rar = self.nzb.rars[0]
#     total = rar.total_bytes
#     done = rar.downloaded_bytes
#     remaining = total - done
#     delta = Datetime.Now() - self.download_start_time
#     try:
#       bps = float(done) / float(delta.seconds)
#     except:
#       bps = 1
#     
#     try:
#       secs_left = int(float(remaining) / bps)
#     except:
#       secs_left = 999999
#     log(7, funcName, 'seconds left:', secs_left)
    return self.secs_left
  
  @property
  def fullPathToMediaFile(self):
    funcName = '[Queue.MediaItem.fullPathToMediaFile]'
    fullPath = False
    for name in self.files:
      index = name.rfind('.')
      if index > -1:
        ext = name[index+1:]
        if ext in media_extensions:
          log(5, funcName, 'Found this file, returning full path:', Core.storage.join_path(self.completed_path, name))
          fullPath = Core.storage.join_path(self.completed_path, name)
          break
    else:
      log(5, funcName, 'Could not find a media file')
    log(7, funcName, 'Returning:', fullPath)
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
          log(5, funcName, 'Found this file, returning full path:', Core.storage.join_path(self.completed_path, name))
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
#       for name in self.files: #Core.storage.list_dir(self.completed_path):
#         index = name.rfind('.')
#         if index > -1:
#           ext = name[index+1:]
#           if ext in media_extensions:
#             log(6, funcName, "Found media file:", name)
      mediaFile = self.fullPathToMediaFile
      if self.complete:
        filesize = None
      else:
        filesize = self.files[self.mediaFileName]
      log(6, funcName, "initiating Stream.LocalFile with mediaFile:", mediaFile, "and moredata:", (not self.complete), "and size:", filesize)
#             app.stream_initiator = Stream.LocalFile(
#               Core.storage.join_path(self.completed_path, name),
#               more_data_coming = (not self.complete),
#               size = filesize
#             )
      app.stream_initiator = Stream.LocalFile(
	    mediaFile,
	    more_data_coming = (not self.complete),
	    size = filesize
      )
      log (6, funcName, "initiated stream")
      #break
    log(6, funcName, "returning stream_initiator:", app.stream_initiator)
    return app.stream_initiator
  
  def fileCompleted(self, filename):
    funcName = "[queue.MediaItem.fileCompleted]"
    fileExists = False
    try:
      fileExists = Core.storage.file_exists(Core.storage.join_path(self.incoming_path, filename))
      if fileExists:
        log(6, funcName, "Found file:", filename)
      else:
        log(6, funcName, "File not found:", filename)
    except:
      log(6, funcName, "Error when looking for file:", filename)
    return fileExists

  def add_incoming_file(self, filename, data):
    funcName = "[Queue.MediaItem.add_incoming_file]"
    self.incoming_files.append(filename)
    Core.storage.save(Core.storage.join_path(self.incoming_path, filename), data)
    log(6, funcName,"Saved incoming data file", filename, "for item with id", self.id)
    self.unpack(filename)
    self.save()

  def unpack(self, filename):
    funcName = "[Queue.MediaItem.unpack]"
    global app
    unpackerExists = False
    try:
      if not app.unpacker:
        pass
      elif app.unpacker.item.id != self.id:
        pass
      else:
        unpackerExists = True
    except:
      pass
    
    if not unpackerExists:
      log(6, funcName, 'Unpacker does not exist, creating one')
      app.unpacker = Unpacker(self)
      log(7, funcName, 'Getting contents of unpacker')
      self.files = app.unpacker.get_contents()
      log(7, funcName, 'Contents of unpacker:', self.files)
      if filename != self.nzb.rars[0].name:
        log(7, funcName, 'filename is not the first rar in the list')
        app.unpacker.add_part(self.nzb.rars[0].name)
        app.unpacker.add_part(filename)
      log(7, funcName, 'starting unpacker')
      app.unpacker.start()
      log(7, funcName, 'unpacker started')
    else:
      log(6, funcName, 'Adding file to existing unpacker')
      app.unpacker.add_part(filename)
      
    #self.save()
        
  def finished_unpacking(self):
    funcName = "[Queue.MediaItem.finished_unpacking]"
    log(6, funcName, 'Setting item complete to true for id:', self.id)
    self.complete = True
    app.unpacker = None
    log(5, funcName, "Finished unpacking item with id", self.id, "removing incoming data files")
    
    Core.storage.remove_tree(Core.storage.join_path(self.incoming_path))
    
    #for filename in Core.storage.list_dir(self.incoming_path):
    #  Core.storage.remove(Core.storage.join_path(self.incoming_path, filename))
    
#     if app.stream_initiator and app.stream_initiator.more_data_coming:
#       log(6, funcName, 'Updating stream_initiator.more_data_coming to False')
#       app.stream_initiator.more_data_coming = False
#       #self.stream_initiator.size = None
    self.save()

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
      self.items = NWQueue('mediaItems')
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