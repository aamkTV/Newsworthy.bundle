from fileSystem import FS

class Updater(object):
  def __init__(self):
    self.versionCheckURL = "http://www.newzworthy.info/updater/versioncheck.php"
    self.bundleName = "Newzworthy.bundle"
    self.version  = 0.81
    self.lastCheckTime = None
    self.lastData = None
    self.serverDataTimeout = 180
    self.file_system = FS()
    #########################################################################################
    # Version 0.55
    # Change: Use Plex HTTP caching for IMDB and TVRage requests.
    #
    # Version 0.54
    # Fix: Downloads should start correctly
    #
    # Version 0.532
    # Fix: Better handling of malformed NZB files
    # Fix: Better recovery (par2) handling
    # Fix: Tweaks to logging, to reduce and reclassify certain log messages
    # Fix: Fixed an migration function which caused log error, but no real errors
    # Change: Made it quicker to push out changes
    #
    # Version 0.531
    # New: Ability to recover lost queue items from saved queue items on disk
    # 
    # Verion 0.53
    # Fix: Movies section acts like TV (context menu)
    # Fix: Better handling of poorly formed nzb files
    # 
    # Version 0.51
    # Fix: Play button doesn't do as many wierd things anymore.  Had to move Cancel and Delete functions to context menus.
    # New: Multiple NNTP (News) servers.  Automatically retry between them.
    # New: Migrator to new NNTP dict structure
    #
    # Version 0.42
    # Fix: Improperly assembled NZB files (e.g. missing segments in the file) results in hanging downloads.
    # Fix: Installation failed
    #
    # Version .41
    # Fix: If cached data is lost, downloaded items are inaccessable.  Removed dependency on Dict for downloaded item data.  Still check Dict first, but use the item's saved data if the cached data is unavailable.
    # Fix: Newzworthy restarted after changing any preferences.
    # Fix: Logs were getting filled up with JSON error (thanks superpea)
    # New: Removed queue and item dependency on the slow and unreliable Dict
    #      - Prior version users must run the Data Migrator.
    # New: Timeouts connecting to nntp server are treated like missing articles.  The connections are retried a few times, then the article is skipped.
    # New: Much improved handling of damaged files.  Added ability to recover manually if it didn't complete, and to extract if that never completed.
    # New: Ability to change log level in the preferences.  Only advanced users should change this, or if you're requested by Newzworthy developers.
    # New: Reduce the size of saved data when downloading is complete, making start up and scanning faster
    # New: Lots of performance impacts.  (I want to know about slow-downs or memory issues)
    ##########################################################################################
    #self.serverJSON = self.serverData()
  
  @property
  def serverJSON(self):
    if not (self.lastCheckTime) or ((Datetime.Now() - self.lastCheckTime).seconds > self.serverDataTimeout):
      self.lastData = self.serverData()
      self.lastCheckTime = Datetime.Now()
    else:
      return self.lastData
    return self.lastData
 
  @property
  def updateDir(self):
#    return Core.storage.join_path(Core.storage.data_path, "updates")
    return self.file_system.data_sub_folder('update')

  @property
  def stableVersion(self):
    funcName = '[Updater.stableVersion]'
    if self.serverJSON:
      stable = self.serverJSON["stableVersion"]
    else:
      stable = self.version
    log(3, funcName, "stable:", stable)
    return stable
    
  @property
  def betaVersion(self):
    funcName = '[Updater.betaVersion]'
    if self.serverJSON:
      if self.serverJSON["betaVersionExists"]:
        beta = self.serverJSON["betaVersion"]
      else:
        beta = False
    else:
      beta = False
    log(3, funcName, 'beta:', beta)
    return beta
    
  def serverData(self):
    funcName = '[Updater.serverData]'
    try:
      log(3, funcName, 'Getting current server version update data')
      resp = JSON.ObjectFromURL(self.versionCheckURL)
    except:
      resp = None
    return resp
    
  @property
  def updateNeeded(self):
    funcName = '[Updater.updateNeeded]'
    needed = False
    if self.version < self.stableVersion: needed = True
    return needed
  
  @property
  def stableUpdateURL(self):
    funcName = '[Updater.updateURL]'
    url = self.serverJSON["stableVersionURL"]
    return url
    
  def downloadStable(self, dir):
    funcName = '[Updater.downloadStable]'
    log(6, funcName, 'downloading update')
    update = HTTP.Request(self.stableUpdateURL)
    log(6, funcName, 'update downloaded, saving')
    location = self.file_system.save_file(dir, self.stableVersionFilename, update)
    #Core.storage.save(Core.storage.join_path(dir, self.stableVersionFilename), update)
    log(6, funcName, 'saved update', location)
    return location
  
  @property
  def stableVersionFilename(self):
    return self.stableUpdateURL[self.stableUpdateURL.rfind("/")+1:]
    
  def unzipFoldername(self, file):
    foldername = file[:file.rfind(".zip")]
    return foldername

  def updateToStable(self):
    funcName = '[Updater.updateToStable]'
    
    # Make sure the update folders exist
    Core.storage.make_dirs(self.updateDir)
    
    # Download the file and get the location of the downloaded file
    downloadedFile = self.downloadStable(self.updateDir)
    log(3, funcName, 'downloaded file:', downloadedFile)
    
    ###########################################################
    # Skipping this and trying to unzip over itself instead.
    #
    # unzipFolder = Core.storage.join_path(self.updateDir, self.unzipFoldername(downloadedFile))
    # drop the .zip and create a folder for the unzipped files
    # self.unzipUpdate(downloadedFile, unzipFolder)
    #
    # Get a list of the files downloaded and unzipped
    # self.updateFiles(unzipFolder)
    ###########################################################
    
    ###########################################################
    # Unzipping directly over the current plugin contents
    # 
    unzipFolder = Core.storage.join_path(self.pluginDir)
    log(5, funcName, 'Unzipping to', unzipFolder)
    self.unzipUpdate(downloadedFile, unzipFolder)
    log(6, funcName, 'Unzipped', downloadedFile, 'to', unzipFolder)
    #
    ###########################################################
  def unzipUpdate(self, pathToFile, pathToUpdate):
    funcName = '[Updater.unzipUpdate]'
    info = Helper.Run('unzip','-o', pathToFile, '-d', pathToUpdate)
  
  @property
  def pluginDir(self):
    return self.file_system.pluginDir
  
  @property
  def pluginContentsDir(self):
    funcName = '[Updater.pluginContentsDir]'
    dir = self.pluginDir + self.bundleName + "/Contents/"
    return dir
  
  def updateFiles(self, pathToFiles):
    funcName = '[Updater.updatedFiles]'
    filesUpdated = False
    walk = Storage.walk(pathToFiles)
    for root, dirs, files in walk:
      if root.count("Contents") < 1: continue
      relativePath = root[root.rfind("Contents"):]
      for file in files:
        fileNeedsUpdating = compareFile(file, relativePath, pathToFiles)
        if fileNeedsUpdating:
          originalLocation, newFileLocation = fileNeedsUpdating
          Core.storage.copy(newFileLocation, originalLocation)
          filesUpdated = True
    return filesUpdated
    
  def checkIfFileUpdated(fileName, path, unzipFolder):
    originalLocation = Core.storage.join_path(pluginContentsDir, path, fileName)
    newFileLocation = Core.storage.join_path(self.unzipFolder, path, fileName)
    origMD5 = Helper.Run("md5", originalLocation)
    newMD5 = Helper.Run("md5", newFileLocation)
    if origMD5 != newMD5:
      return originalLocation, newFileLocation
    else:
      return False
    
