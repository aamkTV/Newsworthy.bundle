#from PMS import *
from decoder import Decoder

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
    
    self.item_queue = NWQueue('itemQueue')
    self.article_queue = NWQueue('articleQueue')
    
    self.active_clients = 0
    self.pause = False
    
    self.start_download_thread()
    
  def download(self, item):
    self.item_queue.put(item)
  
  def stop_download_thread(self):
    self.pause = True
  
  def restart_download_thread(self):
    self.pause = False
    self.start_download_thread()
    return True
  
  def start_download_thread(self):
    Thread.Create(self.download_thread)
    return True
      
  def download_thread(self):
    funcName="[Downloader.download_thread]"
    while not self.pause:
    #while len(self.item_queue)>=1:
      log(6, funcName, "running")
      if not self.pause and len(self.item_queue)>0:
        log(6, funcName, 'Length of item queue:',len(self.item_queue))
        item = self.item_queue.get()
        if not item:
          break
      
        self.start_clients()
        
        while not self.pause:
          item.downloading = True
          file_tasks = []
          log(6, funcName,'All the files to download in this task:',item.nzb.rars)
          for file_obj in item.nzb.rars:
            print file_obj
            file_tasks.append(self.download_file(file_obj))
      
          while len(file_tasks) > 0:
            task = file_tasks.pop(0)
            filename, data = task.result
            Log("Finished downloading '%s'", filename)
            item.add_incoming_file(filename, data)
        
          item.downloading = False
          self.item_queue.remove(item)
        
          try:
            item = self.item_queue.get()#(block = False)
          except:
            break
          
        self.shutdown_clients()
  
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
    
    while not self.pause:
      info = self.article_queue.get()
      if not info:
        break
      
      article = client.get_article(info.article_obj)
      info.decoder.add_part(article)
      info.article_obj.complete = True
      self.article_queue.remove(info)
      
    client.disconnect()
    
    Thread.AcquireLock(self.client_lock)
    self.active_clients = self.active_clients -1
    Log("Shutting down a client (%d now running)", self.active_clients)
    Thread.ReleaseLock(self.client_lock)
    
    
  def download_file_task(self, file_obj):
    decoder = Decoder()
    Thread.AcquireLock(self.article_lock)
    for article_obj in file_obj.articles:
      self.article_queue.put(DownloadInfo(file_obj, article_obj, decoder))
    Thread.ReleaseLock(self.article_lock)
    decoder.wait()
    return (decoder.filename, decoder.decoded_data)
