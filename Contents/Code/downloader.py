from decoder import Decoder
import sys
import time

SLEEP_TIME = 5 #seconds between loops when there's nothing to do
FILE_POOL = 2
class Client_Task_Manager(AppService):
  pass

class DownloadInfo(object):
  def __init__(self, file_obj, article_obj, decoder, item):
    self.file_obj = file_obj
    self.article_obj = article_obj
    self.decoder = decoder
    self.item = item
  def __repr__(self):
    return "File:" + str(self.file_obj) + '\nArticle:' + str(self.article_obj) + "\nItem:" + str(self.item)

class Downloader(AppService):
  def init(self):
    self.client_pool = Core.runtime.create_taskpool(self.app.num_client_threads)
    self.file_pool = Core.runtime.create_taskpool(FILE_POOL)
    self.file_tasks = []
    self.client_lock = Thread.Lock()
    self.article_lock = Thread.Lock()
    self.time_slept = 0
######################################################
# Trying to persist queues.  not working so using a thread.queue
#     if persistentQueuing:
#       #self.item_queue = NWQueue('itemQueue')
#       self.article_queue = NWQueue('articleQueue')
#       #self.article_queue = Thread.Queue()
#     else:
#       #self.item_queue = Thread.Queue()
#       self.article_queue = Thread.Queue()
#
    self.article_queue = Thread.Queue()
######################################################    
    self.active_clients = 0
    self.notPaused = True
    
    self.start_download_thread(resume=False)
    self.item = None
  
  def resetArticleQueue(self):
    funcName = "[Downloader.resetArticleQueue]"
    try:
      Thread.AcquireLock(self.article_lock)
      self.article_queue = Thread.Queue()
    except:
      log(1, funcName, 'Could not reset article queue.  Error', sys.exc_info()[1])
    finally:
      Thread.ReleaseLock(self.article_lock)
    
    try:
      self.file_pool = Core.runtime.create_taskpool(FILE_POOL)
    except:
      log(1, funcName, 'Could not reset file pool')
  
  def stop_download_thread(self):
    funcName = '[Downloader.stop_download_thread]'
    self.notPaused = False
    #log(7, funcName, self.client_pool[0])
    self.shutdown_clients()
    try:
      if self.item.id: self.app.unpacker_manager.end_unpacker(self.item.id)
    except:
      log(1, funcName, 'Error:', sys.exc_info()[1])
    #self.client_pool = Core.runtime.create_taskpool(self.app.num_client_threads)

  
  def restart_download_thread(self):
    self.notPaused = True
    Thread.Create(self.start_download_thread, resume=True)
    return True
  
  def start_download_thread(self, resume=False):
    funcName = "[Downloader.start_download_thread]"
    if self.notPaused:
      log(5, funcName, 'Starting download Thread')
      Thread.Create(self.download_thread, resume=resume)
    return True
      
  def download_thread(self, resume=False):
    #from common import log, loglevel
    funcName="[Downloader.download_thread]"
    log(6, funcName, 'self.notPaused state:', self.notPaused)
    resuming = resume
    while self.notPaused:
      log(9, funcName, 'length of downloadingItems:', len(self.app.queue.downloadingItems))
      log(9, funcName, 'length of downloadQueue:', len(self.app.queue.downloadQueue))
      while self.notPaused and len(self.app.queue.downloadableItems)>0:
        #if len(self.app.queue.downloadingItems) > 0:
        #  item = self.app.queue.downloadingItems[0]
        #  log(6, funcName, 'Resuming, getting items that began downloading but did not complete:', item.id)
        #else:
        if True:
          #item = self.app.queue.downloadQueue[0]
          item = self.app.queue.dl_Queue[0]
          log(6, funcName, 'Found this item that needs to be downloaded:', item.id)
      
#         if item:
#           item.download_start_time = Datetime.Now()
#           item.save()
#         else:
#           log(6, funcName, "Didn't get an item.")
#           continue
        
        if item: self.item = item
        
        log(6, funcName, 'Starting clients')
        self.client_pool = Core.runtime.create_taskpool(int(self.app.num_client_threads))
        self.start_clients()
        
        while self.notPaused and item:
          item.downloading = True
          item.save()
          self.file_tasks = []
          try:
            log(7, funcName,'All the files to download in this task:',item.nzb.rars)
            #skippedFile = False
            self.add_files_to_download(item.nzb.rars, item)
            log(4, funcName, 'Now I\'ll wait for files to download')
          except:
            log(1, funcName, 'No files to download!')
            pass
          item.download_start_time = Datetime.Now()
          item.save()
          while len(self.file_tasks) > 0:
            log(6, funcName, 'Number of files in the process:', len(self.file_tasks))
            log(7, funcName, 'Checking status of file')
            task = self.file_tasks.pop(0)
            filename, data = task.result
            #filename = task.result
            log(6, funcName, "Finished downloading", filename)
            item.add_incoming_file(filename, data)
            #item.add_incoming_file(filename)
            
          if item.valid:
            log(7, funcName, 'Setting item.downloading to False')
            item.downloading = False
            log(7, funcName, 'Setting item.downloadComplete to True')
            item.downloadComplete = True
            item.save()
            item = False
            #self.item_queue.remove(item)
          
        log(6, funcName, 'Shutting down clients')
        self.shutdown_clients()
      
      else: #not self.notPaused or item_queue<1
        log(8, funcName, 'Nothing to download, going to sleep for', SLEEP_TIME, '.  Active clients:', self.active_clients)
        if self.active_clients > 0:
          self.resetArticleQueue()
        time.sleep(int(SLEEP_TIME))
        
  
  def add_files_to_download(self, file_objs, item):
    funcName = '[downloader.Downloader.add_files_to_download]'
    skippedFile = False
    for file_obj in file_objs:
      filename = str(file_obj.name)
      log(9, funcName, "If file isn't already downloaded, we'll download it now:", filename)
      if not item.fileCompleted(filename):
        log(6, funcName, 'Adding a file to file_tasks:', file_obj.name)
        self.file_tasks.append(self.download_file(file_obj, item))
      else:
        log(8, funcName, 'Skipping file, already downloaded:', file_obj.name)
        skippedFile = True
      
    if skippedFile and not item.failing and not self.app.unpacker_manager.get_unpacker(item.id):
      log(7, funcName, 'File was skipped, start the unpacker')
      item.unpack(item.nzb.rars[0])
      
  def download_file(self, file_obj, item):
    return self.file_pool.add_task(
      self.download_file_task,
      kwargs = dict(
        file_obj = file_obj,
        item = item
      )#,important = True
    )    
  
  
  def start_clients(self):
    funcName = '[downloader.Downloader.start_clients]'
    log(6, funcName, 'start_clients started')
    Thread.AcquireLock(self.client_lock)
    for x in range(self.app.num_client_threads - self.active_clients):
      self.client_pool.add_task(self.client_task)#, important=True)
      log(7, funcName, 'added a client_task to the client pool:')
    Thread.ReleaseLock(self.client_lock)
    
  def shutdown_clients(self):
    #pass
    Thread.AcquireLock(self.client_lock)
    for x in range(self.active_clients):
      self.article_queue.put(None)
    Thread.ReleaseLock(self.client_lock)
    time.sleep(3)
    self.app.nntpManager.disconnect_all()

#    for client in self.app.nntpManager.clients:
#      try:
#        client.disconnect()
#      except:
#        pass
      
  def client_task(self):
    funcName = "[downloader.Downloader.client_task]"
    Thread.AcquireLock(self.client_lock)
    self.active_clients = self.active_clients + 1
    funcName = "[downloader.Downloader.client_task " + str(self.active_clients) + "]"
    client = None
    try:
      log(8, funcName, 'self.client_lock obtained, creating client')
      client = nntpClient(self.app)
      #client = self.app.nntpManager.get_available_client()
      client.connect()
      log(8, funcName, 'client created, self.client_lock releasing')
    except:
      ex, err, tb = sys.exc_info()
      log(1, funcName, 'unable to connect to nntp', err)
    finally:
      Thread.ReleaseLock(self.client_lock)
    
    info=None
    while self.notPaused and client:
      log(9, funcName, 'Top of outer loop')
      #failed = False
      info=None
      try:
        info = self.article_queue.get(True, 60)
        info.article_obj.failed = False
        log(7, funcName, 'info:', info)
      except:
        log(8, funcName, 'Nothing in the article queue')
        break
      if not info:
        log(8, funcName, 'Did not get an article info')
        break
      
      log(8, funcName, 'Getting file:', info.file_obj.name, ', article:', info.article_obj.article_id)
      try:
        if client.sock:
          article = client.get_article(info.article_obj)
        else:
          raise nntpException("Connection closed", 1003)
      except nntpException:
        type, exception, traceback = sys.exc_info()
        if exception.id == 430:
          log(2, funcName, 'article', info.article_obj.article_id, 'failed to download')
          if self.notPaused:
            info.article_obj.failed = True
            #item = self.app.queue.downloadingItems[0]
            info.item.add_failed_article(info.article_obj.article_id)
            info.decoder.skip_part(info.article_obj.segment_number)
            continue
          else:
            break
        elif exception.id == 1003:
          log(3, funcName, 'Error downloading:', exception)
          if exception.id == 1003:
            break
      except:
        log(1, funcName, 'Error!', sys.exc_info()[1])
        break
      if self.notPaused:
        log(9, funcName, 'top on inner loop')
        if not info.article_obj.failed:
          #log(9, funcName, 'Sending data to decoder:', article)
          info.decoder.add_part(article, info.article_obj.segment_number)
          info.article_obj.complete = True
        else:
          log(8, funcName, 'Article failed:', info.article_obj.article_id)
        log(9, funcName, 'bottom of inner loop')
      elif not self.notPaused:
        if info:
          if info.decoder:
            if not info.decoder.stopped:
              log(8, funcName, 'Stopped decoder (1) for', info.file_obj.name)
              info.decoder.stopped = True
      log(9, funcName, 'bottom of outer loop')
    else:
      log(3, funcName, 'self.notPaused:', self.notPaused, '/client:', client)
    if not self.notPaused:
      if info:
        if info.decoder:
          if not info.decoder.stopped:
            info.decoder.stopped = True
            log(8, funcName, 'Stopped decoder (2) for', info.file_obj.name)
    if info:
      if info.decoder:
        if not info.decoder.stopped:
          info.decoder.stopped = True
          log(8, funcName, 'Stopped decoder (3) for', info.file_obj.name)
    else:
      log(8, funcName, 'Nothing to decode')
    log(8, funcName, 'After all loops, next thing is to disconnect clients')
    #time.sleep(1)
    try:
      client.disconnect()
    except:
      ex, err, tb = sys.exc_info()
      log(3, funcName, 'Error disconnecting client:', err)
    
    Thread.AcquireLock(self.client_lock)
    self.active_clients = self.active_clients -1
    log(6, funcName, "Shutting down a client (" + str(self.active_clients) + " now running)")
    Thread.ReleaseLock(self.client_lock)

  ##############################################################################  
  def download_file_task(self, file_obj, item):
    funcName = "[Downloader.download_file_task]"
    log(6, funcName, 'Downloading file:', file_obj.name)
    decoder = Decoder(item, file_obj)
    try:
      Thread.AcquireLock(self.article_lock)
      for article_obj in file_obj.articles:
        self.article_queue.put(DownloadInfo(file_obj, article_obj, decoder, item))
        log(9, funcName, 'self.article_queue.qsize():', self.article_queue.qsize())
    except:
      log(1, funcName, 'Error adding articles to queue')
    finally:
      Thread.ReleaseLock(self.article_lock)
    log(7, funcName, 'Waiting for decoder to complete for file', file_obj.name)
    decoder.wait()
    log(7, funcName, 'downloaded filename:', decoder.filename, 'size:', len(decoder.data))
    #Core.storage.save(Core.storage.join_path(item.incoming_path, decoder.filename), decoder.data)
    #saver = Saver(item.incoming_path, decoder.filename, decoder.data)
    #saver.save()
    #log(7, funcName, 'saved file:', decoder.filename)
    #return (decoder.filename, decoder.decoded_data)
    if file_obj in item.nzb.rars:
      if item.nzb.rars[item.nzb.rars.index(file_obj)].name != decoder.filename:
        log(3, funcName, 'Updating item nzb rars file to', decoder.filename)
        item.nzb.rars[item.nzb.rars.index(file_obj)].name=decoder.filename
    if file_obj in item.nzb.pars:
      if item.nzb.pars[item.nzb.pars.index(file_obj)].name != decoder.filename:
        log(3, funcName, 'Updating item nzb pars file to', decoder.filename)
        item.nzb.pars[item.nzb.pars.index(file_obj)].name=decoder.filename
      
    item.save()
    return decoder.filename, decoder.data
