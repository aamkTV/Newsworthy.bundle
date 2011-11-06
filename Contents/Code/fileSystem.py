#import os

class FS(object):
  def __init__(self):
    pass
    
  @property
  def pluginDir(self):
    funcName = '[fileSystem.pluginDir]'
    tokens = Core.storage.data_path.split("/")
    dir = "/"
    for token in tokens:
      if len(token) < 1: continue
      if token == "Plug-in Support":
        break
      else:
        dir += token + "/"
    dir += "Plug-ins/"# + self.bundleName + "/Contents/"
    return dir

  def data_sub_folder(self, foldername):
    return Core.storage.join_path(Core.storage.data_path, foldername)

  def save_file(self, folder, filename, data):
    Core.storage.save(Core.storage.join_path(folder, filename), data)
    return Core.storage.join_path(folder, filename)
    
  def show_folder_contents(self, folder):
    return Core.storage.list_dir(folder)
    
  @property
  def root_folder(self):
    root_path = ""
    if Platform.OS == "MacOSX":
      root_path = "/Volumes"
    elif Platform.OS == "Windows":
      # somehow running echo list volume | diskpart would be handy to get a list of drives
      pass
    elif Platform.OS == "Linux":
      # haven't given this any research.  Maybe the same as MacOSX
      pass
    return root_path

  def folder_available(self, folder):
    funcName = '[fileSystem.folder_available]'
    if folder:
      try:
        if Core.storage.dir_exists(folder):
          return True
        else:
          return False
      except:
        log(5, funcName, 'Error:', sys.exc_info()[1])
        return False
    else:
      log(5, funcName, 'No folder to check for existence')
      return False
