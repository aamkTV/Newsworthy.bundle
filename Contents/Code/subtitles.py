import struct, os, sys, zipfile
from common import *

class Subtitles(object):
  def __init__(self, file_path=None, filesize=0):
    funcName = 'Subtitles.__init__'
    log(7, funcName, 'file_path:', file_path, 'filesize:', filesize)
    self.OS = openSubTitlesOrg(file_path, filesize)
    self.SearchByOSHashAndFileSize = self.OS.SearchByHashAndFileSize
    self.subtitles = self.OS.subtitles
    self.DownloadSub = self.OS.DownloadSub
    
class openSubTitlesOrg(object):
  def __init__(self, file_path=None, filesize=0):
    self.name = 'openSubTitlesOrg'
    self.file_path = file_path
    self.filesize = os.path.getsize(self.file_path)
    self.hash = self.hashFile(self.file_path)
    self.xmlrpc_proxy = XMLRPC.Proxy(url='http://api.opensubtitles.org/xml-rpc')
    self.agent_name = 'Newzworthy'
    self.version = "v1"
    self.user_agent = self.agent_name + "_" + self.version
    self.token = None
    self.searchURL = 'http://www.opensubtitles.org/en/search/'
    self.language = "sublanguageid-eng"
    self.subtitles = [] 
  
  def hashFile(self, name): 
    funcName = self.name + '.hashFile'
    try: 
      longlongformat = 'q'  # long long 
      bytesize = struct.calcsize(longlongformat) 
                    
      #f = open(name, "rb")
      #f = Core.storage.load(name)
      log(1, funcName, 'name:', name)
      fd = os.open(name, os.O_RDONLY)
      f = os.fdopen(fd, 'r')
      #log(1, funcName, 'f:', f)
      hash = self.filesize

      if self.filesize < 65536 * 2: 
        return "SizeError" 
                 
      for x in range(65536/bytesize): 
        buffer = f.read(bytesize) 
        (l_value,)= struct.unpack(longlongformat, buffer)  
        hash += l_value 
        hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number  
                         
    
      f.seek(max(0,self.filesize-65536),0) 
      for x in range(65536/bytesize): 
        buffer = f.read(bytesize) 
        (l_value,)= struct.unpack(longlongformat, buffer)  
        hash += l_value 
        hash = hash & 0xFFFFFFFFFFFFFFFF 
                 
      f.close()
      #fd.close()
      returnedhash =  "%016x" % hash 
      log(7, funcName, 'OSHash:', returnedhash)
      return returnedhash 
    
    except: 
      log(1, funcName, 'Error:', sys.exc_info()[1])
      raise
  
  def Login():
    funcName = self.name + ".Login"
    try:
      response = self.xmlrpc_proxy.LogIn('','','', self.agent_name)
      if not response['status'] == "200 OK":
        log(1, funcName, 'Error logging in:', response['status'])
        raise Exception("Unable to login to OpenSubtitles")
      
      self.token = response['token']
    except:
      log(1, funcName, 'Error:', sys.exc_info()[1])
      return False
    
    return True
  
  def SearchByHashAndFileSize(self, file=None, hash=None, size=0):
    funcName = self.name + ".SearchByHashAndFileSize"
    subs = []
#   try:
#     params = {
#               'moviehash': self.hash,
#               'moviebytesize': self.filesize
#              }
#     response = self.xmlrpc_proxy.SearchSubtitles(self.token, params)
    try:
      if not size: size = self.filesize
      if not hash: hash = self.hash
      url = self.searchURL + self.language + "/moviebytesize-%s/moviehash-%s/simplexml" % (size, hash)
      log(7, funcName, 'URL:', url)
      xmlResponse = XML.ElementFromURL(url)
      try:
        log(9, funcName, XML.StringFromElement(xmlResponse))
        subtitles = xmlResponse.xpath("//subtitle")
        for sub in subtitles:
          downloadURL = sub.xpath('download')[0].text
          log(7, funcName, 'Found download URL:', downloadURL)
          subs.append(downloadURL)
      except:
        log(1, funcName, 'Error retrieving subtitles:', sys.exc_info()[1])
    except:
      log(1, funcName, 'Error searching for subtitles:', sys.exc_info()[1])
    self.subtitles = subs
    return subs
  
  
  def DownloadSub(self, subsToDownload=None, save_location=None, downloadedSubs=[]):
    funcName = self.name + ".DownloadSub"
    if not save_location:
      raise Exception("Nowhere to save downloaded subtitle files")
    if isinstance(subsToDownload, list):
      for sub in subsToDownload:
        downloadedSubs = self.DownloadSub(subsToDownload=sub, save_location=save_location, downloadedSubs=downloadedSubs)
    if subsToDownload and isinstance(subsToDownload, str):
      downloaded_sub = HTTP.Request(subsToDownload)
      log(8, funcName, 'downloaded_sub.headers:', downloaded_sub.headers)
      attachment_info = downloaded_sub.headers['Content-Disposition']
      # Header format: Content-Disposition: attachment; filename="chuck.chuck.vs.the.zoom.(2011).eng.1cd.(4263921).zip"
      filename = attachment_info[attachment_info.index("=")+1:].replace("\"","")
      log(7, funcName, 'Saving subtitle file:', filename, 'in location:', save_location)
      saved_file = Core.storage.join_path(save_location, filename)
      Core.storage.save(saved_file, downloaded_sub)
      zfile = zipfile.ZipFile(saved_file, mode="r")
      log(7, funcName, 'zipfile contents:', zfile.namelist())
      zfiles = zfile.namelist()
      for zipped_file in zfiles:
        log(7, funcName, 'Examining zipped file:', zipped_file)
        ext = zipped_file[-3:]
        if ext in subtitle_extensions:
          log(7, funcName, 'Extracting:', zipped_file)
          #This won't work until Plex upgrades to Python 2.6
          #zfile.extract(zipped_file, save_location)
          #Workaround for Python 2.5
          #zfile.open(zipped_file, 'r')
          sub_file = zfile.read(zipped_file)
          Core.storage.save(Core.storage.join_path(save_location, zipped_file), sub_file)
          downloadedSubs.append(zipped_file)
      Core.storage.remove(saved_file)
    else:
      sub_to_download = self.subtitles[0]
      downloadedSubs = self.DownloadSub(subsToDownload=[sub_to_download], save_location=save_location, downloadedSubs=downloadedSubs)
    return downloadedSubs
