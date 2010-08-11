from report import Report
from unpacker import Unpacker
from nzbf import NZB
#from common import AppService

media_extensions = ['avi', 'mkv', 'mov']

class MediaItem(object):
  def __init__(self, queue, nzbID, report, nzb_xml):
    funcName = "[queue.MediaItem.__init__]"
    self.queue = queue
    self.id = nzbID
    self.report = report
    self.nzb = NZB(nzb_xml)
    log(5, funcName, "making", self.incoming_path)
    Core.storage.make_dirs(self.incoming_path)
    log(5, funcName, "making", self.completed_path)
    Core.storage.make_dirs(self.completed_path)
    
    self.unpacker = None
    self.files = None
    self.stream_initiator = None
    
    self.downloading = False
    self.complete = False
    
    self.download_start_time = None
    
    self.incoming_files = []
    
    report_path = self.path('ReportData')
    nzb_path = self.path('SourceData')
    if not Core.storage.file_exists(nzb_path):
      Core.storage.save(nzb_path, XML.StringFromElement(nzb_xml))
    #if not Core.storage.file_exists(report_path):
    #  Core.storage.save(report_path, XML.StringFromElement(report_el))
    
  def path(self, subdir):
    funcName = "[queue.MediaItem.path]"
    log(5, funcName, 'returning this folder:', self.queue.media_path, self.id, subdir)
    return Core.storage.join_path(self.queue.media_path, self.id, subdir)
    
  @property
  def incoming_path(self):
    return self.path('Incoming')
  
  @property
  def completed_path(self):
    return self.path('Completed')
    
  @property
  def play_ready(self):
    return self.complete or (self.unpacker != None and self.unpacker.play_ready)
    
  @property
  def play_ready_percent(self):
    if self.play_ready:
      return 100
    else:
      return self.nzb.rars[0].percent_done
  
  @property
  def play_ready_time(self):
    if not self.download_start_time:
      return
    
    rar = self.nzb.rars[0]
    total = rar.total_bytes
    done = rar.downloaded_bytes
    remaining = total - done
    delta = Datetime.Now() - self.download_start_time
    bps = float(done) / float(delta.seconds)
    try:
      secs_left = int(float(remaining) / bps)
    except:
      secs_left = 999999
    return secs_left
  
  @property
  def stream(self):
    if not self.stream_initiator and self.play_ready and self.files:
      print self.files
      for name in self.files: #Core.storage.list_dir(self.completed_path):
        index = name.rfind('.')
        if index > -1:
          ext = name[index+1:]
          if ext in media_extensions:
            print "Found media file: %s" % name
            
            if self.complete:
              filesize = None
            else:
              filesize = self.files[name]
            
            self.stream_initiator = Stream.LocalFile(
              Core.storage.join_path(self.completed_path, name),
              more_data_coming = (not self.complete),
              size = filesize
            )
            break
    return self.stream_initiator
    
  def add_incoming_file(self, filename, data):
    self.incoming_files.append(filename)
    Core.storage.save(Core.storage.join_path(self.incoming_path, filename), data)
    Log("Saved incoming data file '%s' for item with id %s", filename, self.id)
    
    self.unpack(filename)
      
  def unpack(self, filename):
    if not self.unpacker:
      if filename != self.nzb.rars[0].name:
        raise Exception('Trying to create an unpacker with a file other than the first rar (\'%s\', should be \'%s\')', filename, self.nzb.rars[0].name)
      self.unpacker = Unpacker(self)
      self.files = self.unpacker.get_contents()
      self.unpacker.start()
    else:
      self.unpacker.add_part(filename)
    
  def finished_unpacking(self):
    self.complete = True
    self.unpacker = None
    Log("Finished unpacking item with id '%s'; removing incoming data files", self.id)
    for filename in Core.storage.list_dir(self.incoming_path):
      Core.storage.remove(Core.storage.join_path(self.incoming_path, filename))
      
    if self.stream_initiator and self.stream_initiator.more_data_coming:
      self.stream_initiator.more_data_coming = False
      self.stream_initiator.size = None
      
  def download(self):
    funcName = '[queue.MediaItem.download]'
    log(4, funcName, 'Starting Download')
    if not (self.complete or self.downloading):
      self.download_start_time = Datetime.Now()
      self.queue.app.downloader.download(self)
      log(4, funcName, 'Item sent to downloader.download')
    
class Queue(AppService):
  def init(self):
    funcName = "[Queue.init]"
    log(4, funcName, 'Setting media path to', Core.storage.data_path, '/Media')
    self.media_path = Core.storage.join_path(Core.storage.data_path, 'Media')
    log(4, funcName, 'Making sure', self.media_path, 'exists')
    Core.storage.make_dirs(self.media_path)
    log(4, funcName, 'Initializing items')
    self.items = NWQueue('MediaItems')
    
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
    
  def add(self, nzbID, nzbService, article):
    """Gets the NZB file's URL, gets the report information, creates a MediaItem object, puts it in the queue, and tells the file to start downloading"""
    funcName = "[Queue.add]"
    #report_el = nzbService.report(report_id)
    log(4, funcName, 'Received ID:', nzbID, 'NZBService:', nzbService)
    log(4, funcName, 'Getting NZB XML for', article.title)
    nzb_xml = XML.ElementFromURL(nzbService.downloadNZBUrl(nzbID))
    log(6, funcName, 'Got this xml:', XML.StringFromElement(nzb_xml))
    item = MediaItem(self, nzbID, article, nzb_xml)
    log(5, funcName, 'Adding this to the queue.  Items in queue:', len(self.items))
    self.items.append(item)
    log(5, funcName, 'Item added to queue.  Items in queue:', len(self.items))
    item.download()
    return item