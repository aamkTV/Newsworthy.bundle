class Updater(object):
  def __init__(self):
    self.versionCheckURL = "http://www.newzworthy.info/updater/versioncheck.php"
    self.bundleName = "Newzworthy.bundle"
    self.version  = .3
    #######################
    #
    # Next version requires a new version of media items with the following new attributes:
    # self.recoverable
    # self.recovery_complete
    # self.failed_articles
    # self.repair_percent
    #
    # TODO: Write a migration function
    ########################
    self.serverJSON = self.serverData()
  
  @property
  def updateDir(self):
    return Core.storage.join_path(Core.storage.data_path, "updates")

  @property
  def stableVersion(self):
    funcName = '[Updater.stableVersion]'
    stable = self.serverJSON["stableVersion"]
    log(3, funcName, "stable:", stable)
    return stable
    
  @property
  def betaVersion(self):
    funcName = '[Updater.betaVersion]'
    if self.serverJSON["betaVersionExists"]:
      beta = self.serverJSON["betaVersion"]
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
    update = HTTP.Request(self.stableUpdateURL)
    #filename = self.stableUpdateURL[self.stableUpdateURL.rfind("/")+1:]
    Core.storage.save(Core.storage.join_path(dir, self.stableVersionFilename), update)
    return Core.storage.join_path(dir, self.stableVersionFilename)
  
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
    unzipFolder = Core.storage.join_path(self.pluginContentsDir)
    self.unzipUpdate(downloadedFile, unzipFolder)
    #
    ###########################################################
  def unzipUpdate(self, pathToFile, pathToUpdate):
    funcName = '[Updater.unzipUpdate]'
    info = Helper.Run('unzip','-o', pathToFile, '-d', pathToUpdate)
  
  def pluginContentsDir(self):
    funcName = '[Updater.contentsDir]'
    tokens = self.updateDir.split("/")
    dir = "/"
    for token in tokens:
      if len(token) < 1: continue
      if token == "Plug-in Support":
        break
      else:
        dir += token + "/"
    
    dir += "Plug-ins/" + self.bundleName + "/Contents/Test"
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
    