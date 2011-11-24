from report import Report
from unpacker import Unpacker
from nzbf import NZB
from Recoverer import Recoverer
import time
import shutil
import sys
import subtitles
from configuration import *
from common import *
#from common import AppService

app = None

class MediaItem(object):
  global app
  def __init__(self, nzbID, report, nzb_xml, skipXML=False):
#  def __init__(self, queue, nzbID, report, nzb_xml):
    funcName = "[queue.MediaItem.__init__]"
    #self.queue = queue
    self.id = nzbID
    self.report = report
    if not skipXML:
      #log(5, funcName, 'Creating nzb object for:', nzb_xml)
      self.nzb = NZB(nzb_xml)
      
    self.valid = True
    self.failed_articles = []
    self.failure_detected = False
    #self.save_lock = Thread.Lock()
    self.archiving = False
    self.archived = False

    self.files = None
    
    self.recoverable = False
    self.recovery_complete = False
    self.repair_percent = 0
    self.recovery_files_added = False
    
    self.downloading = False
    self.complete = False
    self.downloadComplete = False
    
    self.download_start_time = None
    
    self.incoming_files = []
    self.media_path = Core.storage.join_path(Core.storage.data_path, 'Media')
    self.ensure_storage_dirs()      
      

    if not hasattr(self,"nzb_path"):
      log(5, funcName, 'No nzb_path stored, generating a new one')
      self.nzb_path = Core.storage.join_path(self.incoming_path, cleanFileName(str(self.report.title) + '.nzb'))
    else:
      log(5, funcName, 'Existing nzb_path:', self.nzb_path)
    if not Core.storage.file_exists(self.nzb_path):
      if not skipXML:
        Core.storage.save(self.nzb_path, XML.StringFromElement(nzb_xml))
    if not skipXML and self.nzb:
      self.check_for_missing_segments()
    elif not skipXML and not self.nzb:
      raise Exception("No NZB Downloaded")
    self.save()
  
  def init(self):
    funcName = '[queue.MediaItem.init]'
    
  def ensure_storage_dirs(self):
    funcName = '[queue.MediaItem.ensure_storage_dirs]'
    log(5, funcName, "making", self.incoming_path)
    Core.storage.ensure_dirs(self.incoming_path)
    log(5, funcName, "making", self.completed_path)
    Core.storage.ensure_dirs(self.completed_path)
  
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
    #if not self.failure_detected: self.failure_detected = True
    if not self.recovery_files_added:
      self.recovery_files_added = True
      self.add_pars_to_download()
      self.save()

  def check_for_missing_segments(self):
    funcName = '[Queue.MediaItem.check_for_missing_segments]'
    @parallelize
    def find_missing_segments():
      for file in self.nzb.rars:
        @task
        def check_file(thisFile=file):
          n = 1
          log(7, funcName, 'Checking for missing segment numbers:', thisFile.name, thisFile.segment_numbers)
          for segment_number in thisFile.segment_numbers:
            if segment_number != n:
              log(3, funcName, thisFile.name, ': missing segment number:', n)
              self.add_failed_article(n)
            n += 1

  def delete(self):
    funcName = '[Queue.MediaItem.delete]'
    self.valid = False
    try:
      up = app.unpacker_manager.get_unpacker(self.id)
      if up: app.unpacker_manager.end_unpacker(self.id)
      if app.recoverer:
        if app.recoverer.item.id == self.id:
          app.recoverer.stopped = True
          app.recoverer = None
    except:
      log(6, funcName, 'Unable to stop unpacker or recoverer')

    #myPath = Core.storage.join_path(self.media_path, str(self.report.mediaType), cleanFSName(self.report.title))
    myPath = self.path('')
    myPath = myPath[:-1]
    log(5, funcName, 'Deleting path:', myPath)
    try:
      Core.storage.remove_tree(myPath)
    except:
      log(1, funcName, 'Unable to remove item path:', myPath)
    try:
      Core.storage.remove(self.nzb_path)
    except:
      log(1, funcName, 'Unable to remove NZB path:', self.nzb_path)
    #log(5, funcName, 'Deleting path:', self.nzb_path)
    #Core.storage.remove_tree(self.nzb_path)
    time.sleep(1)
    self.remove()
    return True
  
  def archive_filename(self, file):
    funcName = '[queue.MediaItem.archive_filename]'
    archive_filename = self.archive_basename + file[-4:]
    return archive_filename
  
  @property
  def archive_basename(self):
    funcName = '[queue.MediaItem.archive_basename]'
    if self.report.mediaType == 'Movie':
      archive_filename = cleanFileName(self.report.title)
    elif self.report.mediaType == 'TV':
      try:
        archive_filename = self.report.metadata['seriesName']
        if 'season' in self.report.metadata:
          archive_filename += " S" + str(self.report.metadata['season']) + "E" + str(self.report.metadata['episode'])
        if 'episode_title' in self.report.metadata: archive_filename += " - " + self.report.metadata['episode_title']
        archive_filename = cleanFileName(archive_filename)
      except:
        log(3, funcName, 'Error:', sys.exc_info()[1])
        archive_filename = cleanFileName(self.report.title)
    return archive_filename
  
  @property
  def archive_path(self):
    funcName = '[queue.MediaItem.archive_path]'
    #log(1, funcName, 'FSConfigDict:', FSConfigDict)
    if self.report.mediaType == 'Movie':
      try:
        archive_path = getConfigValue(FSConfigDict, MOVIE_ARCHIVE_FOLDER)
        if not Core.storage.dir_exists(archive_path): raise Exception("Archive folder not available")
      except:
        log(1, funcName, 'Error getting archive path:', sys.exc_info()[1])
      if not archive_path: raise Exception("No Movie Archive Path found in configuration")
    elif self.report.mediaType == 'TV':
      try:
        archive_path = getConfigValue(FSConfigDict, TV_ARCHIVE_FOLDER)
        #log(1, funcName, '*****TEST:', Dict[FSConfigDict])
        if not archive_path: raise Exception("No TV Archive Path found in configuration")
        if not Core.storage.dir_exists(archive_path): raise Exception("Archive folder not available")
        archive_path = Core.storage.join_path(archive_path, cleanFileName(self.report.metadata['seriesName']))
        if 'season' in self.report.metadata:
          archive_path = Core.storage.join_path(archive_path, "Season " + str(self.report.metadata['season']))
      except:
        log(3, funcName, 'Error:', sys.exc_info()[1])
        archive_path = getConfigValue(FSConfigDict, 'TV')
        if not archive_path: raise Exception("No Archive Path found in configuration")
        if not Core.storage.dir_exists(archive_path): raise Exception("Archive folder not available")
        archive_path = Core.storage.join_path(archive_path, cleanFileName(self.report.title))
    return archive_path
          
  def archive(self, delete=False):
    funcName = '[queue.MediaItem.archive]'
    self.archiving = True
    archive_path = self.archive_path
    archive_filename = self.archive_filename(self.mediaFileName)
    full_archive_location = Core.storage.join_path(archive_path, archive_filename)
    try:
      if self.archive_path:
        Core.storage.ensure_dirs(archive_path)
        log(5, funcName, 'Saving', self.fullPathToMediaFile, 'to', full_archive_location)
        Core.storage.copy(self.fullPathToMediaFile, full_archive_location)
        if Core.storage.file_size(self.fullPathToMediaFile) == Core.storage.file_size(full_archive_location):
          self.archived = True
        else:
          log(1, funcName, 'Archived(' + str(Core.storage.file_size(full_archive_location)) + ') and original (' + str(Core.storage.file_size(self.fullPathToMediaFile)) + ') file sizes do not match!  Item:', self.report.title)
          self.archived = False
          try:
            Core.storage.remove(full_archive_location)
          except:
            log(1, funcName, 'Error removing archived file:', sys.exc_info()[1])
    except:
      log(3, funcName, 'Error archving:', sys.exc_info()[1])
      self.archived = False
    finally:
      #Core.storage.save(archive_path, media_file_data)
      self.archiving = False
      self.save()
    
    #Save subtitles
    
    if self.archived:
      try:
        filelist = Core.storage.list_dir(self.completed_path)
        for fl in filelist:
          ext = fl[-3:]
          if ext in subtitle_extensions:
            try:
              path_to_sub = Core.storage.join_path(self.completed_path, fl)
              sub_archive_path = Core.storage.join_path(archive_path, self.archive_filename(fl))
              log(5, funcName, 'Copying Subtitle:', fl, 'to', sub_archive_path)
              Core.storage.copy(path_to_sub, sub_archive_path)
            except:
              log(1, funcName, 'Error copying subtitle', fl, 'Error:', sys.exc_info()[1])
      except:
        log(1, funcName, 'Error attempting to find and archive subtitles:', sys.exc_info()[1])

      try:
        if delete:
          self.delete()
      except:
        log(1, funcName, 'Error deleting after archiving:', sys.exc_info()[1])
  
 
  def path(self, subdir):
    funcName = "[queue.MediaItem.path]"
    #log(5, funcName, 'returning this folder:', self.media_path, self.id, subdir)
    path = Core.storage.join_path(self.media_path, str(self.report.mediaType), cleanFSName(self.report.title), subdir)
    if self.complete and not Core.storage.dir_exists(path):
      log(3, funcName, 'Requested path not found for a completed download.  Trying to recover path from nzb file.  Path requested:', path)
      path_from_nzb_path = self.nzb_path.split("/")[-2]
      log(5, funcName, 'path_from_nzb:', path_from_nzb_path)
      old_path = Core.storage.join_path(self.media_path, str(self.report.mediaType), path_from_nzb_path, subdir)
      log(5, funcName, 'Looking for path:', old_path)
      if Core.storage.dir_exists(old_path):
        log(5, funcName, 'Alternate path exists, using it:', old_path)
        path = Core.storage.join_path(old_path)
      else:
        log(5, funcName, 'Failed to find alternate path:', old_path)
    log(9, funcName, 'requested path type:', subdir, ': path:', path)
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
    if app.unpacker_manager.get_unpacker(self.id):
      if app.unpacker_manager.get_unpacker(self.id).play_ready:
        #log(7, funcName, 'app.unpacker.play_ready')
        if self.fullPathToMediaFile:
          #log(7, funcName, 'self.fullPathToMediaFile:',self.fullPathToMediaFile)
          ready = True
        else:
          log(7, funcName, 'No media file found')
      else:
        log(7, funcName, 'NOT app.unpacker_manager.get_unpacker(self.id).play_ready')
    else:
      pass#log(7, funcName, 'app.unpacker_manager.get_unpacker(self.id) == False')
    if self.complete and self.fullPathToMediaFile:
      ready = True
    #log(7, funcName, 'Returning:', ready)
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
    #log(7, funcName, 'delta:', delta)
    try:
      #log(7, funcName, 'downloaded_bytes:', self.downloaded_bytes, "delta.seconds:", delta.seconds)
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
    #log(8, funcName, self.files)
    possibleFile = []
    for name in self.files:
      index = name.rfind('.')
      if index > 0:
        ext = name[index+1:]
        if ext in media_extensions:
          possibleFile.append(name)
    
    # Check to see if we have more than one media file.
    # If we have more than one, filter out the sample files.
    if len(possibleFile) > 1:
      nonSamplePossible = []
      for name in possibleFile:
        if name.lower().find("sample")==-1:
          nonSamplePossible.append(name)
    elif len(possibleFile) == 1:
      return Core.storage.join_path(self.completed_path, possibleFile[0])
    else:
      log(5, funcName, 'Could not find a media file')
      return ''
    
    # If we've filtered out non sample files, hopefully we're down to just one file.
    # If we still have more than one media file, we'll go with the biggest one...
    if len(nonSamplePossible) != 1:
      return pick_largest_file(nonSamplePossible)
    elif len(nonSamplePossible) == 1:
      return Core.storage.join_path(self.completed_path, nonSamplePossible[0])
    #else:
    #  log(5, funcName, 'Only sample files, pick the largest one')
    #  return pick_largest_file(
          #log(8, funcName, 'Found this file, returning full path:', Core.storage.join_path(self.completed_path, name))
          #fullPath = Core.storage.join_path(self.completed_path, name)
          #break
    #else:
    #  log(5, funcName, 'Could not find a media file')
    log(8, funcName, 'Returning:', fullPath)
    return fullPath
  
  def pick_largest_file(files):
    largest = 0
    largest_name = ''
    for name in files:
      if self.files[name] > largest:
        largest = self.files[name]
        largest_name = name
    return largest_name
    
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
        log(9, funcName, "Found file:", filename)
      else:
        log(9, funcName, "File not found:", filename)
    except:
      log(2, funcName, "Error when looking for file:", filename)
    return fileExists

  def add_incoming_file(self, filename, data):
    funcName = "[Queue.MediaItem.add_incoming_file]"
    if self.valid:
      #cleanFilename = cleanFSName(filename)
      self.incoming_files.append(filename)
            
      saveInBackground = True
      
      saver = Saver(self.incoming_path, filename, data)
      saver.save()
      if saveInBackground:
        Thread.Create(self.saver_monitor, self, saver)
        #Notification('Downloaded', 'Downloaded file:', filename, 2000)
        #saver.wait()
      else:
        self.saver_monitor(saver)
      #log(6, funcName,"Saved incoming data file", filename, "for item with id", self.id)

  def add_to_unpacker(self, filename):
    funcName = "[Queue.MediaItem.add_to_unpacker]"
    if not self.failing:
      log(6, funcName, 'Not failing, unpacking', filename)
      self.unpack(filename)
    elif self.failing:
      if not self.downloading and self.downloadComplete:#len(self.incoming_files) == len(self.nzb.rars):
        log(6, funcName, 'Downloaded final par file:', filename)
        self.recover_par()
        self.save()
    #else:
    #  log(7, funcName, 'No need to save, this file is being deleted')
  
  def saver_monitor(self, saver):
    funcName = '[Queue.MediaItem.saver_monitor]'
    filename = saver.save_filename
    saver.wait()
    log(7, funcName, filename, 'is done saving, adding to unpacker')
    self.add_to_unpacker(filename)
    
  def unpack(self, filename):
    funcName = "[Queue.MediaItem.unpack]"
    global app
    up = app.unpacker_manager.get_unpacker(self.id)
    if not up:
      log(6, funcName, 'Unpacker does not exist, creating one')
      up = app.unpacker_manager.new_unpacker(self.id)
      log(7, funcName, 'Getting contents of unpacker')
      self.files = up.get_contents()
      log(7, funcName, 'Contents of unpacker:', self.files)
      if filename != self.nzb.rars[0].name:
        log(7, funcName, 'filename is not the first rar in the list, using the first file to start unpacker')
        up.add_part(self.nzb.rars[0].name)
        up.add_part(filename)
      log(7, funcName, 'starting unpacker')
      up.start()
      log(7, funcName, 'unpacker started')
    else:
      log(6, funcName, 'Adding file to existing unpacker')
      up.add_part(filename)
  
  @property
  def currently_recovering(self):
    recovering = False
    if not self.complete:
      if app.recoverer != None:
        if app.recoverer.item.id == self.id:
          recovering = True
    return recovering
    
  @property
  def currently_unpacking(self):
    up = app.unpacker_manager.get_unpacker(self.id)
    if up == False:
      return False
    else:
      return True
    
  def finished_unpacking(self):
    funcName = "[Queue.MediaItem.finished_unpacking]"
    if self.failing and self.downloadComplete and not self.recovered:
      # Get the recovery process kicked off
      self.recover_par()
    else:
      log(6, funcName, 'Setting item complete to true for id:', self.id)
      self.downloading = False
      self.downloadComplete = True
      self.complete = True
      app.unpacker_manager.end_unpacker(self.id)
      log(5, funcName, "Finished unpacking item with id", self.id, "removing incoming data files")    
      Core.storage.remove_tree(Core.storage.join_path(self.incoming_path))
      log(5, funcName, 'Removing nzb')
      self.cleanup()
      self.nzb = None
      if Prefs['Autoarchive']:
        try:
          Core.storage.ensure_dirs(self.archive_path)
          self.archive()
        except:
          log(2, funcName, 'Auto Archive on, but could not find storage folders:', sys.exc_info()[1])          
    self.save()
  
  def cleanup(self):
    #self.nzb = None
    file_arrays = [self.nzb.rars, self.nzb.pars]
    for files in file_arrays:
      for nzfile in files:
        nzfile.remove_articles()
    self.save()
    return True
    
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
    Thread.Create(self.recovery_monitor)
    app.recoverer.start()
    
  def recovery_monitor(self):
    funcName = '[Queue.MediaItem.recovery_monitor]'
    r = app.recoverer
    while True:
      if app.recoverer == None: break
      toSave = False
      if r.recoverable:
        if not self.recoverable:
          self.recoverable = True
          toSave = True
        if self.repair_percent != r.repair_percent:
          self.repair_percent = r.repair_percent
          toSave = True
        if toSave: self.save()
      else:
        # The file can't be recovered.  Set the flags and call it a day!
        if r.recovery_complete:
          app.recoverer = None
          self.recoverable = False
          self.recovery_complete = True
          self.save()
          break
          
      # When repairs are completed, unpack and call it a day
      if self.recoverable and r.recovery_complete:
        log(3, funcName, 'Recovery complete, unpacking, saving, and exiting')
        app.recoverer = None
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
    log(5, funcName, 'Saving item:', self.report.title)
    try:
      #Thread.AcquireLock(self.save_lock)
      Data.SaveObject(self.id, self)
      #global app
      app.queue.loadedItems[self.id] = self
    except:
      log(1, funcName, 'Unable to save', self.report.title)
      raise
    finally:
      pass
      #Thread.ReleaseLock(self.save_lock)
    #if persistentQueuing:
    #  if app.queue.getItem(self.id):
    #    app.queue.items.save()
  
  def remove(self):
    Data.Remove(self.id)
    global app
    try:
      del app.queue.loadedItems[self.id]
    except:
      log(1, 'Unable to remove loadedItem:', self.id)

####################################################################################
class Queue(AppService):
  def init(self):
    funcName = "[Queue.init]"
#     log(4, funcName, 'Setting media path to', Core.storage.data_path, '/Media')
#     self.media_path = Core.storage.join_path(Core.storage.data_path, 'Media')
#     log(4, funcName, 'Making sure', self.media_path, 'exists')
#     Core.storage.make_dirs(self.media_path)
    log(4, funcName, 'Initializing items')
    self.items = self.setupQueue(('mediaItems' + mediaItemsQueueVersion))
    self.nzbQueue = self.setupQueue(('nzbDownloads'))
    self.loadedItems = {}
    global app
    app = self.app
  
  def setupQueue(self, name, reset=False):
    funcName = '[Queue.setupQueue]'
    if persistentQueuing:
      ret = NWQueue(name)
    else:
      ret = []
    return ret
    
#   def setupItemQueue(self, reset=False):
#     funcName = '[Queue.Queue.setupItemQueue]'
#     if persistentQueuing:
#       self.items = NWQueue('mediaItems' + mediaItemsQueueVersion)
#     else:
#       items = []
#     return self.items
  
  def resetItemQueue(self):
    if persistentQueuing:
      self.items.reset()
    else:
      self.items = []
      
  def getItem(self, id):
    funcName = "[Queue.getItem]"
    theItem = None
    if not id:
      log(1, funcName, 'Requesting non-existent item:', id)
      return False    
    try:
      theItem = self.loadedItems[id]
    except KeyError:
      try:
        if Data.Exists(id):
          theItem = Data.LoadObject(id)
          self.loadedItems[id] = theItem
      except:
        log(1, funcName, 'Error loading saved item:', id)
        #raise
    except:
      log(1, funcName, 'Error trying to load item:', id)
    if theItem == None:
      log(1, funcName, 'Item:', id, 'not found.')
      return False
    #log(5, funcName, 'Returning item:', theItem.id, theItem.report.title, theItem)
    return theItem
  
  @property
  def downloadingItems(self):
    funcName = '[Queue.downloadingItems]'
    downloadList = []
    for itemID in self.items:
      try:
        item = self.getItem(itemID)
        if (not item.downloadComplete) and item.downloading:
          downloadList.append(item)
      except:
        log(1, funcName, 'Unable to read item, it will be deleted:', item)
        self.items.remove(itemID)
        Data.Remove(itemID)
        self.loadedItems = {}
        continue
    return downloadList
    
  @property
  def downloadQueue(self):
    funcName = '[Queue.downloadQueue]'
    downloadList = []
    for itemID in self.items:
      try:
        item = self.getItem(itemID)
        if (not item.downloadComplete) and (not item.downloading):
          downloadList.append(item)
      except:
        log(1, funcName, 'Unable to read item, it will be deleted:', item)
        self.items.remove(itemID)
        Data.Remove(itemID)
        self.loadedItems = {}
        continue
    return downloadList
  
  @property
  def dl_Queue(self):
    funcName = '[Queue.dl_Queue]'
    dl_list =[]
    for itemID in self.items:
      try:
        item = self.getItem(itemID)
        if (not item.downloadComplete):
          #log(7, funcName, 'Adding', item.report.title, 'to dl_Queue')
          dl_list.append(item)
      except:
        log(1, funcName, 'Unable to read item, it will be deleted:', item)
        self.items.remove(itemID)
        Data.Remove(itemID)
        self.loadedItems = {}
        continue
    return dl_list
  
  @property
  def downloadableItems(self):
    downloadList = []
    #downloadList.extend(self.downloadingItems)
    #downloadList.extend(self.downloadQueue)
    downloadList.extend(self.dl_Queue)
    return downloadList
    
  @property
  def allItems(self):
    list = []
    list.extend(self.completedItems)
    list.extend(self.downloadableItems)
    return list
  
  @property
  def completedItems(self):
    funcName = '[Queue.completedItems]'
    downloadList = []
    for itemID in self.items:
      try:
        item = self.getItem(itemID)
        if item.complete or item.downloadComplete:
          downloadList.append(item)
      except:
        log(1, funcName, 'Unable to read item, it will be deleted:', item)
        self.items.remove(itemID)
        Data.Remove(itemID)
        self.loadedItems = {}
        continue
    return downloadList
  
  @property
  def archivingItems(self):
    funcName = '[Queue.archivingItems]'
    archivingList = []
    for itemID in self.items:
      try:
        item = self.getItem(itemID)
        if hasattr(item, 'archiving'):
          if item.archiving:
            archivingList.append(item)
      except:
        log(3, funcName, 'Error:', sys.exc_info()[1])
        continue
    return archivingList

  @property
  def archivedItems(self):
    funcName = '[Queue.archivedItems]'
    archivedList = []
    for itemID in self.items:
      try:
        item = self.getItem(itemID)
        if hasattr(item, 'archived'):
          if item.archived:
            archivedList.append(item)
      except:
        log(3, funcName, 'Error:', sys.exc_info()[1])
        continue
    return archivedList
  
  @property
  def nzbDownloadQueue(self):
    funcName = '[Queue.nzbDownloadQueue]'
    allArticles = []
    for nzbQueueItem in nzbQueue:
      article = nzbQueueItem.article
      allArticles.append(article)
    return allArticles

  def download_nzb_add_item_to_queue(self):
    """Gets the NZB file's URL, gets the report information, creates a MediaItem object, and puts it on the items queue"""
    funcName = "[Queue.download_nzb_add_item_to_queue]"
    #report_el = nzbService.report(report_id)
    nzbQueueItem = self.nzbQueue.pop()
    log(4, funcName, 'Received ID:', nzbQueueItem.nzbID, 'NZBService:', nzbQueueItem.nzbService)
    nzb_xml = None
    if not nzbQueueItem.skipXML: 
      log(4, funcName, 'Getting NZB XML for', nzbQueueItem.article.title)
      nzb_xml = XML.ElementFromURL(nzbQueueItem.nzbService.downloadNZBUrl(nzbQueueItem.nzbID))
    else:
      log(4, funcName, 'Skipping NZB XML for', nzbQueueItem.article.title)
    #log(7, funcName, 'Got this xml:', XML.StringFromElement(nzb_xml))
    item = MediaItem(nzbQueueItem.nzbID, nzbQueueItem.article, nzb_xml, nzbQueueItem.skipXML)
    log(7, funcName, 'Item to be added to queue:', item)
    log(5, funcName, 'Adding this to the queue.  Items in queue:', len(self.items))
    self.items.append(item.id)
    #log(5, funcName, 'Item added to queue.  Items in queue:', len(self.items))
    #item.download()
    return item

  def add(self, nzbID, nzbService, article, skipXML=False):
    nzbQueueItem = nzbDownload(queue=self, nzbID=nzbID, nzbService=nzbService, article=article, skipXML=skipXML)
    self.nzbQueue.add(nzbQueueItem)
    Thread.Create(self.download_nzb_add_item_to_queue)
    
class nzbDownload(object):
  def __init__(self, queue, nzbID, nzbService, article, skipXML):
    self.queue = queue
    self.nzbID = nzbID
    self.nzbService = nzbService
    self.article = article
    self.skipXML = skipXML
##########################################################################################
class Saver(object):
  def __init__(self, location, filename, data):
    self.save_location = location
    self.save_filename = filename
    self.save_data = data
    self.finished = Thread.Event()
    
  def wait(self):
    self.finished.wait()

  def save(self):
    self.finished.clear()
    Thread.Create(self.save_in_background)
    
  def save_in_background(self):
    funcName = '[Saver.save_in_background]'
    log(7, funcName, 'starting save of file:', self.save_filename)
    Core.storage.save(Core.storage.join_path(self.save_location, self.save_filename), self.save_data)
    log(7, funcName, 'saved file:', self.save_filename)
    self.finished.set()
