from decoder import Decoder
import time

SLEEP_TIME = 1 #seconds between loops when there's nothing to do
        
class DownloadInfo(object):
  def __init__(self, file_obj, article_obj, decoder):
    self.file_obj = file_obj
    self.article_obj = article_obj
    self.decoder = decoder


class Downloader(AppService):
  def init(self):
    self.client_pool = Core.runtime.create_taskpool(self.app.num_client_threads)
    self.file_pool = Core.runtime.create_taskpool(1)
    
    self.client_lock = Thread.Lock()
    self.article_lock = Thread.Lock()
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
  
  def resetArticleQueue(self):
    funcName = "[Downloader.resetArticleQueue]"
    try:
      Thread.AcquireLock(self.article_lock)
######################################################    
# Part of persistent queueing
#       if persistentQueuing:
#         self.article_queue=NWQueue('articleQueue')
#       else:
#         self.article_queue=Thread.Queue()
#
      self.article_queue=Thread.Queue()
######################################################
    except:
      log(1, funcName, 'Could not reset article queue')
    finally:
      Thread.ReleaseLock(self.article_lock)
    
    try:
      self.file_pool = Core.runtime.create_taskpool(1)
    except:
      log(1, funcName, 'Could not reset file pool')

  def download(self, item):
    #self.item_queue.put(item)
    #log(6, 'self.app.queue.items count:', len(self.app.queue.items))
    pass
  
  def stop_download_thread(self):
    funcName = '[Downloader.stop_download_thread]'
    self.notPaused = False
    #log(7, funcName, self.client_pool[0])
    self.shutdown_clients()
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
      log(7, funcName, 'length of downloadingItems:', len(self.app.queue.downloadingItems))
      log(7, funcName, 'length of downloadQueue:', len(self.app.queue.downloadQueue))
      #log(6, funcName, 'resuming:', resuming)
    #while len(self.item_queue)>=1:
      #log(6, funcName, "running")
      #if self.notPaused and (len(self.item_queue)>0 or resume):
      while self.notPaused and len(self.app.queue.downloadableItems)>0:
#      while self.notPaused and ( (len(self.app.queue.downloadingItems) + len(self.app.queue.downloadQueue))>0 or resuming ):
        if len(self.app.queue.downloadingItems) > 0:
          item = self.app.queue.downloadingItems[0]
          log(6, funcName, 'Resuming, getting items that began downloading but did not complete:', item.id)
        else:
          item = self.app.queue.downloadQueue[0]
          log(6, funcName, 'Found this item that needs to be downloaded:', item.id)
        
        if item:
          item.download_start_time = Datetime.Now()
          item.save()
        else:
          log(6, funcName, "Didn't get an item.")
          continue
                    
        log(6, funcName, 'Starting clients')
        self.start_clients()
        
        while self.notPaused and item:
          item.downloading = True
          item.save()
          file_tasks = []
          log(7, funcName,'All the files to download in this task:',item.nzb.rars)
          for file_obj in item.nzb.rars:
            #print file_obj
            filename = str(file_obj.name)
            log(7, funcName, "If file isn't already downloaded, we'll download it now:", filename)
            if not item.fileCompleted(filename):
              log(6, funcName, 'Adding a file to file_tasks:', file_obj.name)
              file_tasks.append(self.download_file(file_obj))
            else:
              log(6, funcName, 'Skipping file, already downloaded:', file_obj.name)

          while len(file_tasks) > 0:
            log(6, funcName, 'Number of files in the process:', len(file_tasks))
            log(7, funcName, 'Checking status of file')
            task = file_tasks.pop(0)
            filename, data = task.result
            log(6, funcName, "Finished downloading", filename)
            item.add_incoming_file(filename, data)
          
          log(7, funcName, 'Setting item.downloading to False')
          item.downloading = False
          log(7, funcName, 'Setting item.downloadComplete to True')
          item.downloadComplete = True
          item.save()
          item = False
          #self.item_queue.remove(item)
          
#           try:
#             item = self.app.queue.items.get()#(block = False)
#           except:
#             break
        log(6, funcName, 'Shutting down clients')
        self.shutdown_clients()
      
      else: #not self.notPaused or item_queue<1
        log(7, funcName, 'Nothing to download, going to sleep for', SLEEP_TIME)
        time.sleep(int(SLEEP_TIME))
  
  def download_file(self, file_obj):
    return self.file_pool.add_task(
      self.download_file_task,
      kwargs = dict(
        file_obj = file_obj,
      ),
      important = True
    )    
  
  
  def start_clients(self):
    Thread.AcquireLock(self.client_lock)
    for x in range(self.app.num_client_threads):
      self.client_pool.add_task(self.client_task, important=True)
    Thread.ReleaseLock(self.client_lock)
    
  def shutdown_clients(self):
    Thread.AcquireLock(self.client_lock)
    for x in range(self.active_clients):
      self.article_queue.put(None)
    Thread.ReleaseLock(self.client_lock)
      
  def client_task(self):
    funcName = "[downloader.Downloader.client_task]"
    Thread.AcquireLock(self.client_lock)
    self.active_clients = self.active_clients + 1
    log(4, funcName, "Starting a client (",self.active_clients,"now running)")
    Thread.ReleaseLock(self.client_lock)
    #client = nntpClient(self.app)
    client = nntpClient()
    client.connect()
    
    while self.notPaused:
      info = self.article_queue.get()
      if not info:
        log(6, funcName, 'Did not get an article info')
        break
      
      log(7, funcName, 'Getting file:', info.file_obj.name, ', article:', info.article_obj.article_id)
      article = client.get_article(info.article_obj)
      
      if self.notPaused:
        info.decoder.add_part(article)
        info.article_obj.complete = True
###############################################
# Part of persistency effort
#       if persistentQueuing:
#         log(6, funcName, 'Finished article:', info.file_obj.name + "." + info.article_obj.article_id, 'removing it from the queue')
#         self.article_queue.remove(info)
###############################################      
    client.disconnect()
    
    Thread.AcquireLock(self.client_lock)
    self.active_clients = self.active_clients -1
    log(6, funcName, "Shutting down a client (" + str(self.active_clients) + " now running)")
    Thread.ReleaseLock(self.client_lock)
    
    
  def download_file_task(self, file_obj):
    funcName = "[Downloader.download_file_task]"
    log(6, funcName, 'Downloading file:', file_obj.name)
    decoder = Decoder()
    Thread.AcquireLock(self.article_lock)
    for article_obj in file_obj.articles:
      self.article_queue.put(DownloadInfo(file_obj, article_obj, decoder))
    Thread.ReleaseLock(self.article_lock)
    decoder.wait()
    return (decoder.filename, decoder.decoded_data)
