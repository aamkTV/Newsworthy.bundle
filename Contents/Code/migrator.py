from time import sleep
from tvrage import TV_RAGE_METADATA as tvrage
import movie_metadata

import sys
#from introspector import *
class Migrator(AppService):
  def init(self):
    #self.migrationNeeded = self.checkForMigrations()
    self.queueToPointFour = False #self.checkForQueueToPointFour()
    self.itemsToPointFour = False #self.checkForItemsToPointFour()
    self.itemsToPointFourOne = False #self.checkForCompletedItemsToPointFourOne()
    self.nntpToPointFiveOne = False #self.check_for_nntp_to_point_five_one()
    self.cacheToPointFiveFive = self.check_and_fix_for_item_cache_to_point_five_five()
    #self.itemsToPointFiveTwo = False
    
  @property
  def migrationNeeded(self):
    return self.checkForMigrations()
  
  def checkForMigrations(self):
    # One function to check for all migration needs
    self.queueToPointFour = self.checkForQueueToPointFour()
    self.itemsToPointFour = self.checkForItemsToPointFour()
    self.itemsToPointFourOne = self.checkForCompletedItemsToPointFourOne()
    self.nntpToPointFiveOne = self.check_for_nntp_to_point_five_one()
    self.item_reports_to_point_six = self.check_for_item_reports_to_point_six()
    self.check_and_fix_point_seven_four()
    if self.queueToPointFour or self.itemsToPointFour or self.itemsToPointFourOne or self.nntpToPointFiveOne or self.item_reports_to_point_six:
      return True
    else:
      return False
  
  def run_migrations(self):
    funcName = '[Migrator.run_migrations]'
    if self.queueToPointFour:
      log(3, funcName, 'Migrating queue')
      self.migrateQueueToPointFour()
    if self.itemsToPointFour:
      log(3, funcName, 'Migrating items')
      self.migrateItemsToPointFour()
    if self.itemsToPointFourOne:
      log(3, funcName, 'Migrating items to 0.41')
      self.migrateItemsToPointFourOne()
      try:
        Dict[nzbItemsDict] = {}
        del Dict['nzbItemsDict']
      except:
        pass
    if self.check_for_nntp_to_point_five_one():
      log(3, funcName, 'Migrating nntp to 0.51')
      self.migrate_nntp_to_point_five_one()
    if self.check_for_item_reports_to_point_six():
      log(3, funcName, 'Migrating item reports to 0.60')
      self.migrate_item_reports_to_point_six()
  
  def check_and_fix_point_seven_four(self):
    funcName = '[Migrator.check_and_fix_point_seven_four]'
    media_dir = Core.storage.join_path(Core.storage.data_path, 'Media')
    tv_dir = Core.storage.join_path(media_dir, 'TV')
    movie_dir = Core.storage.join_path(media_dir, 'Movie')
    dirs = [media_dir, tv_dir, movie_dir]
    for dir in dirs:
      removed = self.removeFilesInDirByExt(dir, '.nzb')
      log(2, funcName, 'Removed', removed, 'nzb files in', dir)
    for itemID in self.app.queue.items:
      item = self.app.queue.getItem(itemID)
      if item.complete and not Core.storage.dir_exists(item.path('')):
        log(2, funcName, 'Removing invalid item:', item.report.title)
        item.remove()
    
  def removeFilesInDirByExt(self, path, ext):
    funcName = '[removeFilesInDirByExt]'
    removed_file_count = 0    
    listing = Core.storage.list_dir(path)
    for file in listing:
      if file[-len(ext):] == ext:
        file_path = Core.storage.join_path(path, file)
        Core.storage.remove(file_path)
        removed_file_count += 1
    return removed_file_count

  def check_for_item_reports_to_point_six(self):
    funcName = '[Migrator.check_for_item_reports_to_point_six]'
    for itemID in self.app.queue.items:
      item = self.app.queue.getItem(itemID)
      try:
        bool(item.report.metadata)
      except AttributeError:
        log(2, funcName, 'Need migration:', funcName)
        if not 'item_reports_migrated_to_point_six' in Dict:
          return True
    return False
  
  def migrate_item_reports_to_point_six(self, noSkip=False):
    funcName = '[Migrator.migrate_item_reports_to_point_six]'
    errors = False
    @parallelize
    def update_metadata():
#    if True:
      for itemID in self.app.queue.items:
        @task
        def update_item_metadata(itemID = itemID):
#        if True:
          try:
            skip = False
            item = self.app.queue.getItem(itemID)
            #report = item.report
            if not noSkip:
              if hasattr(item.report, 'metadata'): skip = True
            log(7, funcName, 'Updating:', item.report.title, ' ID:', itemID)
            if not skip:
              if item.report.mediaType == 'TV':
                item.report.metadata = tvrage(item.report.moreInfoURL).metadata
                # Update TV-specific attributes
                if item.report.metadata['title']: item.report.title = item.report.metadata['title']
                if item.report.metadata['season'] or item.report.metadata['episode'] or item.report.metadata['airDate']:
                  item.report.subtitle = "S" + item.report.metadata['season'] + "E" + item.report.metadata['episode'] + " (" + item.report.metadata['airDate'] + ")"
                
              elif item.report.mediaType == 'Movie':
                # Update movie-specific attributes
                item.report.metadata = movie_metadata.movie_metadata(item.report.moreInfo).metadata
                if item.report.metadata['desc']: item.report.description = item.report.metadata['desc']
                if item.report.metadata['fanart']: item.report.fanart = item.report.metadata['fanart']
                if item.report.metadata['date']: item.report.subtitle = item.report.metadata['date'].strftime('%B %d, %Y')
              
              # Update attributes applicable to all media
              if item.report.metadata['thumb']: item.report.thumb = item.report.metadata['thumb']
              
              item.save()
              log(5, funcName, 'Successfully migrated:', item.report.title)
            else:
              log(5, funcName, 'Skipping:', item.report.title)
          except:
            log(1, funcName, 'Unable to update item:', item.report.title, ' Error:', sys.exc_info()[1])
            errors = True
    if not errors:
      #Dict["item_reports_migrated_to_point_six"] = True
      #Dict.Save()
      time.sleep(1)
      self.checkForMigrations()
    
  def check_and_fix_for_item_cache_to_point_five_five(self):
    funcName = '[Migrator.check_and_fix_for_item_cache_to_point_five_five]'
    dictNames = ["tvRageItemsDict_v1", "imdbItemsDict_v1"]
    #old_cache_found = False
    for dictName in dictNames:
      if dictName in Dict:
        #old_cache_found = True
        log(3, funcName, 'Deleting old dict cache:', dictName)
        del Dict[dictName]
        #Dict.Save()
      
  def check_for_nntp_to_point_five_one(self):
    old_nntp_dict_found = False
    if 'nntpConfigDict_v1' in Dict:
      old_nntp_dict_found = True
    return old_nntp_dict_found
    
  from configuration import nntpServer
  def migrate_nntp_to_point_five_one(self):
    old_dict = Dict['nntpConfigDict_v1']
    new_nntp = nntpServer()
    if 'nntpHost' in old_dict: new_nntp.setHost(old_dict['nntpHost'])
    if 'nntpUsername' in old_dict: new_nntp.setUsername(old_dict['nntpUsername'])
    if 'nntpPassword' in old_dict: new_nntp.setPassword(old_dict['nntpPassword'])
    if 'nntpPort' in old_dict: new_nntp.setPort(old_dict['nntpPort'])
    if 'nntpSSL' in old_dict: new_nntp.setSSL(old_dict['nntpSSL'])
    if 'nntpConnections' in old_dict: new_nntp.setConnections(old_dict['nntpConnections'])
    new_nntp.setPriority(1)
    save_max_connections_setting(query=(int(new_nntp.connections)-1), resetDownloads=False)
    new_nntp.test_connection()
    del Dict['nntpConfigDict_v1']
    #Dict.Save()
    time.sleep(3)
    self.checkForMigrations()
  
  def checkForCompletedItemsToPointFourOne(self):
    funcName = '[Migrator.checkForCompletedItemsToPointFourOne]'
    badItems = False
    for item in self.app.queue.completedItems:
      log(9, funcName, 'checking', item.report.title, 'item.nzb:', item.nzb)
      if item.nzb != None:
        badItems = True
        log(5, funcName, 'Need to migrate completed items to 0.41')
        break
    return badItems
  
  def migrateItemsToPointFourOne(self):
    funcName = '[Migrator.migrateItemsToPointFourOne]'
    for item in self.app.queue.completedItems:
      if item.nzb != None:
        item.nzb = None
        item.save()
    if self.checkForMigrations():
      log(4, funcName, 'More migrations needed')
    else:
      log(4, funcName, 'Migrations complete!')
    #Dict.Save()
    time.sleep(3)    

  def checkForQueueToPointFour(self):
    funcName ='[Migrator.checkForQueueToPointFour]'
    badQueue = False
    dictName = 'NWQueue_mediaItems_queue'
    if dictName in Dict:
      oldItemQueue = Dict[dictName]
      if len(oldItemQueue) > 0:
        badQueue = True
        log(5, funcName, 'Need to migrate Queue to .4')
    return badQueue
  
  def migrateQueueToPointFour(self):
    funcName = '[Migrator.migrateQueueToPointFour]'
    #log(3, funcName, 'Stopping downloader')
    #self.app.downloader.stop_download_thread()
    dictName = 'NWQueue_mediaItems_queue'
    oldItemQueue = Dict[dictName]
    # Don't continuosly save
    #oldItemQueue.saveInterval = 1000
    i = 0
    for item in oldItemQueue:
      self.app.queue.items.append(item)
      i+=1
      log(3, funcName, 'Migrated items:', i)
      #oldItemQueue.remove(item)
    del Dict[dictName]
    if self.checkForMigrations():
      log(4, funcName, 'More migrations needed')
    else:
      log(4, funcName, 'Migrations complete!')
    #Dict.Save()
    time.sleep(3)
    
  def checkForItemsToPointFour(self):
    funcName = '[Migrator.checkForItemsToPointFour]'
    badItems = False
    for item in self.app.queue.items:
      try:
        int(item)
        #Everything's good
      except:
        #potentially a problem
        log(2, funcName, item, 'needs to migrated')
        self.itemsToPointFour = True
        badItems = True
        break
    return badItems
  
  from queue import *
  import newzbin as nzbNewzbin
  import nzbmatrix as nzbNzbmatrix
  def migrateItemsToPointFour(self):
    funcName = '[Migrator.migrateItemsToPointFour]'
    NZBService = None
    i = 0
    curQueue = []
    for item in self.app.queue.items:
      curQueue.append(item)
    for item in curQueue:
      try:
        int(item)
        if not Data.Exists(item):
          item = self.app.queue.getItem(item)
          raise Exception('Need to migrate')
        log(3, funcName, 'item:', item, 'not migrated')
      except:
        log(2, funcName, 'migrating item:', item)
        newItem = self.app.queue.download_nzb_add_item_to_queue(item.id, NZBService, item.report, skipXML=True)
        if hasattr(item, 'valid'): newItem.valid = item.valid
        if hasattr(item, 'failed_articles'): newItem.failed_articles = item.failed_articles
        if hasattr(item, 'media_path'): newItem.media_path = item.media_path
        if hasattr(item, 'files'): newItem.files = item.files
        if hasattr(item, 'recoverable'): newItem.recoverable = item.recoverable
        if hasattr(item, 'recovery_complete'): newItem.recovery_complete = item.recovery_complete
        if hasattr(item, 'repair_percent'): newItem.repair_percent = item.repair_percent
        if hasattr(item, 'recovery_files_added'): newItem.recovery_files_added = item.recovery_files_added
        if hasattr(item, 'downloading'): newItem.downloading = item.downloading
        if hasattr(item, 'complete'): newItem.complete = item.complete
        if hasattr(item, 'downloadComplete'): newItem.downloadComplete = item.downloadComplete
        if hasattr(item, 'download_start_time'): newItem.download_start_time = item.download_start_time
        if hasattr(item, 'incoming_files'): newItem.incoming_files = item.incoming_files
        if hasattr(item, 'nzb_path'): newItem.nzb_path = item.nzb_path
        if hasattr(item, 'nzb'): newItem.nzb = item.nzb
        log(2, funcName, 'Saving new item')
        newItem.save()
        log(2, funcName, 'Removing old item')
        self.app.queue.items.remove(item)
        i+=1
        log(3, funcName, 'Migrated items:', i)
    log(3, funcName, 'Done with migration.', i, 'items migrated')
    if self.checkForMigrations():
      log(5, funcName, 'More migrations needed')
    else:
      log(4, funcName, 'Migrations complete!')
    #Dict.Save()
    time.sleep(3)
