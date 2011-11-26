from common import *
from array import *
from queue import *
from configuration import *
from time import sleep
import sys
from nntpclient import *
import configuration
import dateutil
import datetime
from tvrage import TV_RAGE_METADATA as tvrage
import movie_metadata
from fileSystem import *

nzbServiceInfo = NZBService()
app = NewzworthyApp()
#nzb = None
nntp = None
#loggedInNZBService = False
loggedInNNTP = False

####################################################################################################
def Start():
  funcName = "[Start]"
  log(1, funcName, 'Starting Newzworthy version:', app.updater.version)
  Plugin.AddPrefixHandler(PREFIX, MainMenu, 'Newzworthy', 'icon-default.png', 'art-default.png')
  DirectoryItem.thumb = R('icon-default.png')
  MediaContainer.art = R('art-default.png')
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("Lists", viewMode="List", mediaType="items")
  MediaContainer.title1 = 'Newzworthy'
  MediaContainer.content = 'Items'
  Resource.AddMimeType('video/x-matroska', '.mkv')
  Resource.AddMimeType('video/x-m4v', '.mp4')
  Resource.AddMimeType('video/x-wmv', '.wmv')
  Resource.AddMimeType('video/x-msvideo', '.avi')
  Resource.AddMimeType('video/MP2T', '.ts')

  log(1, funcName, 'Server OS:', Platform.OS, 'CPU:', Platform.CPU)
  
  #Hack##########################
  if not nzbItemsDict in Dict: Dict[nzbItemsDict] = {}
  if not nntpConfigDict in Dict: Dict[nntpConfigDict] = {}
  ##############################
  
  #global loggedInNZBService
  #global nzb
  global app
  primeConnections=True
  if primeConnections:
    NZBServiceSet = setNZBService()
    log(8, funcName, 'NZB Service Set, logging in')
    app.loggedInNZBService = app.nzb.performLogin(nzbServiceInfo)
    log(8, funcName, 'NZB Service login:', app.loggedInNZBService)

  global nntp
  global loggedInNNTP
  
  #log(7, funcName, 'app:', app)

  #log(8, funcName, 'NNTP Username, password, host, port, ssl:', nntp.nntpUsername, nntp.nntpPassword, nntp.nntpHost, nntp.nntpPort, nntp.nntpSSL)
  if primeConnections:
    nntp = nntpClient(app)
    #nntpServerConfig = app.nntpManager.get_client(app.nntpManager.get_server_by_priority(1))
    try:
      loggedInNNTP = nntp.connect()
    except:
      loggedInNNTP = False
    finally:
      if nntp: nntp.disconnect()
  
  log(4, funcName, 'Setting media path to', Core.storage.data_path, '/Media')
  media_path = Core.storage.join_path(Core.storage.data_path, 'Media')
  log(4, funcName, 'Making sure', media_path, 'exists')
  Core.storage.ensure_dirs(media_path)
  Core.storage.ensure_dirs(Core.storage.join_path(media_path, 'TV'))
  Core.storage.ensure_dirs(Core.storage.join_path(media_path, 'Movie'))

    
  log(5, funcName, 'Newzworthy started')
  return True

####################################################################################################
import newzbin as nzbNewzbin
import nzbmatrix as nzbNzbmatrix
import nzbindexnl as nzbNzbIndexNL
def setNZBService(retType='bool'): #valid return types: bool and object
  """
  Uses the NZBService Preference setting to login to the preferred NZB Service provider.
  Use the retType bool to indicate if the login attempt was successful or not.
  Use the retType object to actually return the nzb object. (This is not common)
  """
  funcName='[setNZBService]'
  #global nzb
  #global loggedInNZBService
  global app
  global nzbServiceInfo

  app.loggedInNZBService = False
  serviceImported = False
  app.nzb = None
  serviceName=Prefs['NZBService']
  log(4,funcName,'importing NZBService:', serviceName)

  nzbServiceInfo.newzbinUsername = getConfigValue(theDict=nzbConfigDict, key='newzbinUsername')
  log(6, funcName, 'newzbin Username:', nzbServiceInfo.newzbinUsername)
  nzbServiceInfo.newzbinPassword = getConfigValue(theDict=nzbConfigDict, key='newzbinPassword')
  #log(8, funcName, 'newzbin Password:', nzbServiceInfo.newzbinPassword)
  log(6, funcName, 'Getting nzbMatrix Username')
  nzbServiceInfo.nzbmatrixUsername = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixUsername')
  log(6, funcName, 'nzbMatrix Username:', nzbServiceInfo.nzbmatrixUsername)
  nzbServiceInfo.nzbmatrixPassword = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixPassword')
  #log(8, funcName, 'nzbMatrix Password:', nzbServiceInfo.nzbmatrixPassword)
  ##nzbServiceInfo.nzbmatrixAPIKey = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixAPIKey')


  if serviceName=='Newzbin':
    log(4, funcName, 'importing newzbin')
    #import newzbin as nzb
    app.nzb = nzbNewzbin
    serviceImported = True
  elif serviceName=='NZBMatrix':
    log(4, funcName, 'importing nzbmatrix')
    #import nzbmatrix as nzb
    app.nzb = nzbNzbmatrix
    serviceImported = True
  elif serviceName=='NZBIndex.nl':
    log(4, funcName, 'importing nzbindex.nl')
    app.nzb = nzbNzbIndexNL
    serviceImported = True
  log(4, funcName, serviceName, 'imported:', app.nzb.name)
  if retType == 'bool': return serviceImported
  if retType == 'object': return app.nzb

####################################################################################################
def ValidatePrefs():
  funcName = "[ValidatePrefs] "
  global app
  app.loggedInNZBService = False


####################################################################################################
@route(routeBase + 'SaveDict')
def SaveDict():
  funcName = '[SaveDict]'
  Dict.Save()
  log(3, funcName, 'Dict Saved')
####################################################################################################
@route(routeBase + 'restart')
def RestartNW():
  global app
  try:
    app.nntpManager.disconnect_all()
  except:
    pass
  cdir = app.updater.pluginContentsDir
  plist = Core.storage.join_path(cdir, 'Info.plist')
  plistData = Core.storage.load(plist)
  Core.storage.save(plist, plistData)
  return Message("Restarted", "Newzworthy is restarting.\nRestart can take up to 30 seconds.")
  
####################################################################################################
@route(routeBase + 'webMainMenu')
def webMainMenu():
  funcName = '[webMainMenu]'
  test = 'hello'
  return test
####################################################################################################
@route(routeBase + 'MainMenu')
def MainMenu():
  funcName = '[MainMenu]'
  #global loggedInNZBService
  global nzbServiceInfo
  global loggedInNNTP
  global nntp
  global app
  #global nzb
  global loglevel
  log(1, funcName, 'Client OS:', Client.Platform, 'Protocols:', Client.Protocols)
  loglevel = int(Prefs['NWLogLevel'])
  # Set the right NZB servers to use
  log(5, funcName, 'NZBService:', Prefs['NZBService'])
  if (not app.loggedInNZBService) or app.nzb.name != Prefs['NZBService']:
    log(3, funcName, 'Not logged into NZB Service, doing it now')
    # try to log into the NZB Service...
    #global nzb
    app.nzb = setNZBService(retType='object')
    app.loggedInNZBService = app.nzb.performLogin(nzbServiceInfo, forceRetry=True)
    log(3, funcName + "nzb login:", str(app.loggedInNZBService))
  else:
    log(3, funcName, "Already logged into nzb")
    
  if not loggedInNNTP:
    log(3, funcName, 'Not logged into NNTP, doing it now')
    # try to log into the nntp service
    try:
      nntp = nntpClient(app)
      loggedInNNTP = nntp.connect()
    except:
      err, id, tb = sys.exc_info()
      log(2, funcName, 'Error logging into NNTP:', err, id, tb)
      loggedInNNTP = False
    finally:
      if nntp: nntp.disconnect()
    log(3, funcName, "nntp login:", loggedInNNTP)
  else:
    log(3, funcName, "Already logged into nntp")

  # Empty context menu, since there aren't any useful contextual options right now.
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
  dir = MediaContainer(contextMenu=cm, noCache=True, viewGroup="Lists")
  
  global app
  if app.updater.updateNeeded:
    dir.Append(DirectoryItem(Route(Update), title=L('NW_UPDATE_AVAIL'), summary=app.updater.stableUpdateURL, thumb=R('update.png'), contextKey='a', contextArgs={}))
  if app.updates.show_new:
    dir.Append(DirectoryItem(Route(Show_Updates), title=L('WHATS_NEW'), summary=str(app.updates.whats_new), thumb=R('update.png'), contextKey='a', contextArgs={}))
  # If we recently upgraded we may need migrations
  if app.migrator.migrationNeeded:
    dir.Append(DirectoryItem(Route(Migrations), title=L('CLK_MIGRATE'), thumb=R('update.png'), contextKey='a', contextArgs={}))
    
  if app.loggedInNZBService and loggedInNNTP:
    log(5, funcName, 'Logged in, showing TV & Movie menu options')
    # Sub-menu for TV
    if app.nzb.TV_BROWSING:
      dir.Append(Function(DirectoryItem(BrowseTV, title=("Go to TV"), thumb=R('tv.jpg'), contextKey="a", contextArgs={})))
    elif app.nzb.TV_SEARCH:
      dir.Append(Function(InputDirectoryItem(Search, title=("Search TV"), prompt=("Search TV"), thumb=R('search.png'), contextKey="a", contextArgs={}), category=app.nzb.CAT_TV))      
    # Sub-menu for Movies
    if app.nzb.MOVIE_BROWSING:
      dir.Append(Function(DirectoryItem(BrowseMovies, title=("Go to Movies"), thumb=R('movies.jpg'),contextKey="a", contextArgs={})))
    elif app.nzb.MOVIE_SEARCH:
      dir.Append(Function(InputDirectoryItem(Search, title=("Search Movies"), prompt=("Search Movies"), thumb=R('search.png'), contextKey="a", contextArgs={}), category=app.nzb.CAT_MOVIES))

  else:
    log(5, funcName, 'Not logged in, showing option to update preferences')
    if not app.loggedInNZBService:
      dir.Append(Function(DirectoryItem(configure, title=("Not logged in to " + Prefs["NZBService"]), thumb=R("x_red.png"), contextKey="a", contextArgs={})))
    if not loggedInNNTP:
      dir.Append(DirectoryItem(Route(manageNNTPs), title=("Not logged in to Usenet (NNTP)"), thumb=R("x_red.png"), contextKey="a", contextArgs={}))

  # Show the troubleshooting options.  Not recommended, but can be very useful.
  if bool(Prefs['ShowDiags']):
    dir.Append(DirectoryItem(Route(diagsMenu), title="Troubleshooting/Diagnostics", thumb=R('troubleshooting.png')))
  else:
    log(7, funcName, 'NOT showing (ie. hiding) diagnostic menu options')

  # Show the preferences option
  log(7, funcName, 'Showing Preferences')
  dir.Append(PrefsItem(L("Preferences"), thumb=R('preferences.png'), contextKey="a", contextArgs={}))
  log(7, funcName, 'Showing setup options')
  dir.Append(Function(DirectoryItem(configure, title="Setup servers, archive, usernames, and passwords", thumb=R('configuration.png'), contextKey="a", contextArgs={})))
  log(7, funcName, 'Showing Manage Queue')
  dir.Append(DirectoryItem(Route(manageQueue), title=("Manage Download Queue (" + str(len(app.queue.downloadableItems)) + ")"), thumb=R('download_queue.png'), contextKey="a", contextArgs={}))
  log(7, funcName, 'Showing Completed Queue Management option')
  dir.Append(DirectoryItem(Route(manageCompleteQueue), title=("View Completed Downloads (" + str(len(app.queue.completedItems)) + ")"), thumb=R('check_green.png'), contextKey="a", contextArgs={}))
  if len(app.queue.archivingItems) > 0:
    dir.Append(DirectoryItem(Route(viewArchivingItems), title=("View Archiving Items (" + str(len(app.queue.archivingItems)) + ")"), thumb=R('folder.png'), contextKey="a", contextArgs={}))
  if len(app.queue.archivedItems) > 0:
    dir.Append(DirectoryItem(Route(manageCompleteQueue, filter="Archived"), title=("View Archived Items (" + str(len(app.queue.archivedItems)) + ")"), thumb=R('folder.png'), contextKey="a", contextArgs={}))
  log(7, funcName, 'Show Dir')
  return dir

#####################################################################################################
@route(routeBase + 'diagsMenu')
def diagsMenu():
  funcName = "[diagsMenu]"
  # Empty context menu, since there aren't any useful contextual options right now.
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
  dir = MediaContainer(contextMenu=cm, noCache=True, viewGroup="Lists")

  log(7, funcName, 'Showing diagnostic menu options')
  log(7, funcName, 'Showing update option')
  dir.Append(DirectoryItem(Route(Update), title="Update Newzworthy", thumb=R('update.png')))
  log(7, funcName, 'Showing "Clear the cache"')
  dir.Append(Function(DirectoryItem(clearArticleDict, title="Clear the article dict cache", thumb=R('trashcan.png'), contextKey="a", contextArgs={})))
  dir.Append(DirectoryItem(Route(clearHTTPCache), title='Clear the HTTP Cache', thumb=R('trashcan.png'), contextKey='a', contextArgs={}))
  log(7, funcName, 'Showing "Delete all Downloaded Files"')
  dir.Append(Function(DirectoryItem(deleteAllDownloads, title="Delete all downloaded files", thumb=R('trashcan.png'), contextKey="a", contextArgs={})))
  dir.Append(DirectoryItem(Route(clearAllQueues), title="Clear all the queues", thumb=R('trashcan.png')))
  dir.Append(DirectoryItem(Route(loadItemsFromDisk), title="Load items from disk", thumb=R('analyze.png')))
  dir.Append(DirectoryItem(Route(reloadAllMetaData), title='Reload All Metadata', thumb=R('search.png')))
  log(7, funcName, 'Showing "Show All Dicts"')
  dir.Append(Function(DirectoryItem(showAllDicts, title="Show All Dicts", contextKey="a", thumb=R('search.png'), contextArgs={})))
  dir.Append(Function(DirectoryItem(listAllDicts, title='List All Dicts', contextKey="a", thumb=R('search.png'), contextArgs={})))
  #log(7, funcName, 'Show restart plugin')
  dir.Append(DirectoryItem(Route(SaveDict), title='Save Dict', contextKey='a', contextArgs={}))
  dir.Append(DirectoryItem(Route(resetDownloader), title='Reset Downloader', contextKey='a', contextArgs={}))
  dir.Append(DirectoryItem(Route(RestartNW), title='Restart Newzworthy Plugin', contextKey="a", contextArgs={}))
  return dir

####################################################################################################
@route(routeBase + "Migrations")
def Migrations():
  funcName = '[Migrations]'
  global app
  app.downloader.stop_download_thread()
  app.downloader.resetArticleQueue()
  app.migrator.checkForMigrations()
  app.migrator.run_migrations()
  time.sleep(3)
  app.downloader.resetArticleQueue()
  app.downloader.notPaused = True
  app.downloader.start_download_thread()

@route(routeBase + "Update")
def Update():
  funcName = '[Update]'
  global app
  if app.updater.updateNeeded:
    app.updater.updateToStable()
    message = "Updated to latest (" + str(app.updater.stableVersion) + ")"# available, download at: " + app.updater.stableUpdateURL
    RestartNW()
  else:
    message = "No Updates Available"
  return Message(title="Updater", message=message)

@route(routeBase + 'Show_Updates')
def Show_Updates():
  funcName = '[Show_Updates]'
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
  dir = MediaContainer(contextMenu=cm, noCache=True, viewGroup="Details")
  
  if app.updates.show_new:
    for version in app.updates.whats_new:
      dir.Append(DirectoryItem(Route(StupidUselessFunction, key="a"), title=("Version " + str(version)), subtitle=str(version), summary=app.updates.whats_new[version], contextKey=version, contextArgs={}))
  dir.Sort("title", descending=True)
  return dir
  
####################################################################################################
@route(routeBase + 'About')
def About():
  funcName = '[About]'
  dir = MediaContainer(noCache=False, viewGroup="Details")
  
####################################################################################################
def clearArticleDict(sender):
  funcName = "[clearArticleDict]"
  log(1, funcName, 'articleDict before clearing:', Dict[nzbItemsDict])
  Dict[nzbItemsDict] = {}
  Dict['nzbItemsDict'] = {}
  log(1, funcName, 'articleDict after clearing:', Dict[nzbItemsDict])
  return Message("Cache Cleared", "All cached items have been cleared.")

@route(routeBase + 'clearHTTPCache')
def clearHTTPCache():
  HTTP.ClearCache()
  return Message("HTTP Cache Cleared", "All HTTP Cache Cleared")

@route(routeBase + 'loadItemsFromDisk')
def loadItemsFromDisk():
  funcName = '[loadItemsFromDisk]'
  DataItemsPath = Core.storage.join_path(Core.storage.data_path, 'DataItems')
  log(5, funcName, 'Getting contents of:', DataItemsPath)
  log(5, funcName, 'Currently loaded items:', len(app.queue.allItems))
  DataItems = Core.storage.list_dir(DataItemsPath)
  log(5, funcName, 'Items on disk:', len(DataItems))
  items_loaded = 0
  for di in DataItems:
    try:
      item = Data.LoadObject(di)
      if item:
        if isinstance(item, MediaItem):
          found_in_queue = False
          all_items = app.queue.allItems
          for q_item in all_items:
            if q_item.id == item.id:
              found_in_queue = True
              break
          if not found_in_queue:
            app.queue.items.append(item.id)
            items_loaded+=1
          else:
            log(5, funcName, 'Item already in queue:', item.report.title)
        else:
          log(5, funcName, 'Not a MediaItem item')
      else:
        log(5, funcName, 'Unloadable item')
    except:
      log(5, funcName, di, 'is not an item.  Error:', sys.exc_info()[1])
  return Message("Done", "Loaded " + str(items_loaded) + " items from disk.")

@route(routeBase + 'reloadAllMetaData')
def reloadAllMetaData():
  funcName = '[reloadAllMetaData]'
  global app
  app.migrator.migrate_item_reports_to_point_six(noSkip=True)
  
@route(routeBase + 'clearAllQueues')
def clearAllQueues():
  funcName = "[clearAllQueues]"
  app.queue.resetItemQueue()
  RestartNW()
  app.downloader.resetArticleQueue()
  return Message("Queues Cleared", "All queues have been cleared.")
  
def deleteAllDownloads(sender):
  funcName = "[deleteAllDownloads]"
  media_path = Core.storage.join_path(Core.storage.data_path, 'Media')
  for dir_obj in Core.storage.list_dir(media_path):
    try:
      Core.storage.remove_tree(Core.storage.join_path(media_path, dir_obj))
    except:
      log(3, funcName, 'Could not delete', dir_obj)
  return Message("Files Deleted", "All downloaded files have been deleted.")
####################################################################################################
def showAllDicts(sender):
  funcName = "[showAllDicts]"
  dir = MediaContainer(noCache=True, noHistory=True)
  log(4, funcName, 'Getting the following dicts:', str(Dict))
  for thisDict in Dict:
    log(5, funcName, 'thisDict is:', str(thisDict))
    try:
      dictKeys = Dict[thisDict].keys()
      log(5, funcName, 'working in this dict:', dictKeys)
      theDict = Dict[thisDict]
      log(5, funcName, 'theDict:', theDict)
      for key in dictKeys:
        log(5, funcName, "getting values for key:", key)
        keyTitle = thisDict + ":" + key + ": " + str(theDict[key] + ": " + str(type(theDict[key])))
        dir.Append(Function(DirectoryItem(StupidUselessFunction, title=keyTitle), key=keyTitle, summary=keyTitle))
    except:
      log(5, funcName, str(thisDict), 'not a dict type, assuming it''s a list or other iterable object')
      for item in Dict[thisDict]:
        keyTitle = thisDict + ": " + str(item)
        dir.Append(Function(DirectoryItem(StupidUselessFunction, title=keyTitle), key=keyTitle))
  return dir

####################################################################################################
def listAllDicts(sender):
  funcName = '[listAllDicts]'
  cm = ContextMenu(includeStandardItems=False)
  #cm.Append(DirectoryItem(Route(deleteDict), title=('Delete')))
  cm.Append(Function(DirectoryItem(deleteDict, title='Delete')))
  dir = MediaContainer(contextMenu=cm, noCache=True, noHistory=True)
  for thisDict in Dict:
    dir.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title=thisDict, contextKey=thisDict, contextArgs={}))
  return dir
####################################################################################################
#@route(routeBase + 'deleteDict/{key}')
def deleteDict(sender, key):
  funcName = '[deleteDict]'
  log(3, funcName, 'Deleting dict:', key)
  del Dict[key]
  SaveDict()
  return listAllDicts(key)
####################################################################################################
def BrowseMovies(sender='nothing'):
  # Empty context menu, since there aren't any useful contextual options right now.
  global app
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
  dir = MediaContainer(contextMenu=cm, noCache=True, title2="Movies")

  if app.nzb.supportsGenres():
    dir.Append(Function(DirectoryItem(BrowseMovieGenres, title=("Browse Recent Movies by Genre"), contextKey="a", contextArgs={}), filterBy="Video Genre"))
  else:
    dir.Append(Function(DirectoryItem(SearchMovies, title=("Browse Recent Movies"), contextKey="a", contextArgs={}), value="", title2="All Recent Movies", days=MovieSearchDays_Default, maxResults=str(app.nzb.RESULTS_PER_PAGE)))

  dir.Append(Function(InputDirectoryItem(Search, title=("Search Movies"), prompt=("Search Movies"), thumb=R('search.png'), contextKey="a", contextArgs={}), category="6"))
  return dir
####################################################################################################
def BrowseTV(sender='nothing'):

  global app
  # Empty context menu, since there aren't any useful contextual options right now.
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="No Options")))
  dir = MediaContainer(viewGroup='Lists', contextMenu=cm, noCache=True, title2="TV", noHistory=False, replaceParent=False)
  

  if app.nzb.supportsGenres(): dir.Append(Function(DirectoryItem(BrowseTVGenres, title=("Browse Recent TV by Genre"), contextKey="a", contextArgs={}), filterBy="Video Genre"))
  dir.Append(Function(InputDirectoryItem(Search, title=("Search TV"), prompt=("Search TV"), thumb=R('search.png'), contextKey="a", contextArgs={}), category=app.nzb.CAT_TV))
  try:
    if len(Dict[TVFavesDict])>=1:
      dir.Append(Function(DirectoryItem(BrowseTVFavorites, title=("Browse TV Favorites (1 Day)"), thumb=R('one_day.png'), contextKey="a", contextArgs={}), days="1", sort_by="DATE"))
      dir.Append(Function(DirectoryItem(BrowseTVFavorites, title=("Browse TV Favorites (1 Week)"), thumb=R('one_week.png'), contextKey="a", contextArgs={}), days="7", sort_by="DATE"))
      dir.Append(Function(DirectoryItem(BrowseTVFavorites, title=("Browse TV Favorites (1 Month)"), thumb=R('one_month.png'), contextKey="a", contextArgs={}), days="30", sort_by="DATE"))
      dir.Append(Function(DirectoryItem(BrowseTVFavorites, title=("Browse TV Favorites (All)"), thumb=R('infinity.png'), contextKey="a", contextArgs={}), days="0"))
  except:
    pass
#  if len(app.queue.downloadableItems) >= 1:
#    for item in app.queue.allItems:
#      if item.report.mediaType == 'TV':
#        pass
        
  #Always let the user manage their favorites
  dir.Append(Function(DirectoryItem(ManageTVFavorites, title=("Manage the list of TV Favorites"), contextKey="a", contextArgs={})))  
  return dir

####################################################################################################
def ManageTVFavorites(sender='nothing'):
  funcName = "[ManageTVFavorites] "
  global app
  if TVFavesDict in Dict:
  	log(5, funcName, TVFavesDict, 'exists, not creating')
  	faves = Dict[TVFavesDict]
  else:
    log(5, funcName, TVFavesDict, "doesn't exist, creating")
    Dict[TVFavesDict] = []
    faves = Dict[TVFavesDict]

  sortedFaves = []
  log(6, funcName + "Current contents of " + TVFavesDict + ": " + str(faves))

  #Add a contextual menu to each item to remove it from the favorites
  if len(faves) >= 1:
    cm = ContextMenu(includeStandardItems=False)
    cm.Append(Function(DirectoryItem(RemoveTVFavorite, title='Remove')))
  else:
    cm = ContextMenu(includeStandardItems = False)
    cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))

  #Instantiate the list...
  dir = MediaContainer(viewGroup='Lists', contextMenu=cm, noCache=True, replaceParent=False, noHistory=True)

  #Add a static item as an option to add new favorites
  dir.Append(Function(InputDirectoryItem(AddTVFavorite, title=L("Add a new Favorite"), prompt=L("Add a new Favorite"), thumb=R('plus_green.png'), contextKey="a", contextArgs={})))
  #Show the list of all the current saved favorites
  for title in faves:
    #searchableTitle = "(" + title.replace(" ", "+") + ")"
    sortedFaves.append(title)
  sortedFaves.sort()
  for title in sortedFaves:
    dir.Append(Function(DirectoryItem(SearchTV, title=title, contextKey=title, contextArgs={}), value=app.nzb.concatSearchList([title]), title2=title, days=TVSearchDays_Default, maxResults=str(app.nzb.RESULTS_PER_PAGE)))

  # Handle the case where there aren't any saved favorites
  if len(sortedFaves) < 1:
    dir.Append(Function(DirectoryItem(StupidUselessFunction, title="No Favorites", contextKey="a", contextArgs={})))

  return dir

####################################################################################################
def AddTVFavorite(sender, query):
  funcName = "[AddTVFavorite] "
  log(2, funcName + "Trying to save \"" + query + "\" to the " + TVFavesDict + " dictionary")
  # the returned object should be a list object
  faves = Dict[TVFavesDict]
  log(4, funcName + "Current contents of " + TVFavesDict  + ": " + str(faves))
  if query.lower() not in faves:
    log(3, funcName + "Appending...")
    #query = query.replace("\"", "\\\"")
    faves.append(query.lower())
    log(3, funcName + "Appended, now setting the dictionary")
    Dict[TVFavesDict] = faves
    log(4, funcName + "Saved!")
  else:
  	log(2, funcName + "Duplicate found, not saving.")

  dir = ManageTVFavorites()
  return dir

####################################################################################################
def RemoveTVFavorite(sender, key):
  funcName="[RemoveTVFavorite] "
  log(2, funcName + "Removing favorite: " + key)
  log(5, funcName + "Getting the current list of favorites")
  faves = Dict[TVFavesDict]
  log(5, funcName + "Current list of favorites: " + str(faves))
  log(5, funcName + "Removing \"" + key + "\" from the list")
  faves.remove(key)
  log(3, funcName + "Removed!  Current list of favorites: " + str(faves))
  log(4, funcName + "Saving new list")
  Dict[TVFavesDict] = faves
  log(5, funcName + "Saved!")
  dir = ManageTVFavorites(key)
  return dir

####################################################################################################
def BrowseTVFavorites(sender, days=TVSearchDays_Default, sort_by=None):
  funcName = "[BrowseTVFavorites] "
  global app
  faves=[]
  faves.extend(Dict[TVFavesDict])
  
  if len(faves)>=1:
    try:
      log(4, funcName, 'Retrieved these favorites:',faves)

      #log(3, funcName + "query: " + query)
      return SearchTV(sender=sender, value=faves, title2="Favorites", days=days, sort_by=sort_by)
    except:
      log(1, funcName, 'Error:', sys.exc_info()[1])
      return Message("No favorites", "You have not saved any favorite TV shows to search.\nAdd some favorites and then try again.")
  else:
    return Message("No favorites", "You have not saved any favorite TV shows to search.\nAdd some favorites and then try again.")

####################################################################################################
def SearchTV(sender, value, title2, days=TVSearchDays_Default, maxResults=str(0), offerExpanded=False, expandedSearch=False, page=1, invertVideoQuality=False, allOneTitle=False, sort_by=None, key=None):
  funcName = "[SearchTV] "
  global app
  
  # Determine if we will be consolidating duplicates to a single entry
  if allOneTitle:
    consolidateDuplicates = False
  else:
    consolidateDuplicates = Prefs['consolidateTVDuplicates']
    
  if isinstance(value, str):
    value = [value]

  #queryString = value # <-- This is a []

  # I'm searching TV, I know the category
  #category = app.nzb.CAT_TV

  nzbItems = Dict[nzbItemsDict]
  allTitles = []

  #make a meaningful title for the window
  thisTitle = "TV > "
  if page>1: thisTitle += "Page " + str(page) + " > "
  thisTitle += title2
  
  log(7, funcName, 'Adding contextual menus')
  dir_replace_parent = False
  cm = ContextMenu(includeStandardItems=False)
  if sort_by == None:
    cm.Append(Function(DirectoryItem(SearchTV, title=L('SORT_NAME')), value=value, title2=title2, days=days, maxResults=maxResults, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by='NAME'))
    cm.Append(Function(DirectoryItem(SearchTV, title=L('SORT_DATE')), value=value, title2=title2, days=days, maxResults=maxResults, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by='DATE'))
  elif sort_by == 'NAME':
    cm.Append(Function(DirectoryItem(SearchTV, title=L('SORT_UNSORTED')), value=value, title2=title2, days=days, maxResults=maxResults, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by=None))
    cm.Append(Function(DirectoryItem(SearchTV, title=L('SORT_DATE')), value=value, title2=title2, days=days, maxResults=maxResults, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by='DATE'))
    dir_replace_parent = True
  elif sort_by == 'DATE':
    cm.Append(Function(DirectoryItem(SearchTV, title=L('SORT_UNSORTED')), value=value, title2=title2, days=days, maxResults=maxResults, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by=None))
    cm.Append(Function(DirectoryItem(SearchTV, title=L('SORT_NAME')), value=value, title2=title2, days=days, maxResults=maxResults, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by='NAME'))
    dir_replace_parent = True
  
  log(7, funcName, 'Creating dir')
  dir = MediaContainer(viewGroup='Details', title2=thisTitle, noHistory=False, noCache=False, replaceParent=dir_replace_parent, contextMenu=cm)
  log(7, funcName, 'Getting the data')
  # Go get the data
  try:
    allEntries = app.nzb.search(category=app.nzb.CAT_TV, query_list=value, period=app.nzb.calcPeriod(days), page=page)
  except:
    log(1, funcName, 'Error searching:', sys.exc_info()[1])
    return Message('Error searching', "There was an error trying to search.\nPlease try again later or check your\nusername, password, and membership status.")
  if not len(allEntries)>=1:
    return Message(header="No Matching Results", message="Your search did not yield any matches")

  saveDict = True

  # See if there are dupes, if we are interested in consolidating them
  if consolidateDuplicates:
    dupesFound, listOfUniques, listOfDupes = checkForDupes(allEntries)
    log(4, funcName, "dupesFound:", dupesFound)
    log(4, funcName, "listOfDuplicates:", listOfDupes)
    log(4, funcName, "listOfUniques:", listOfUniques)
  else:
  	dupesFound = 0
  	listOfUniques = []
  	listOfDupes = []

  @parallelize
  def doTVMetaDataLookups(cm=cm):

    for entry in allEntries:
      @task
      def IterableElement1(thisArticle = entry, all_cm=cm):

        # Check to see if this is a duplicate and we should be de-duping
        # First pass will handle creating all the main entries e.g. no dupes or no de-duping enabled
        if allOneTitle or (consolidateDuplicates and thisArticle.title in listOfUniques) or not consolidateDuplicates:

          if not thisArticle.nzbID in nzbItems:

            thisArticle.mediaType = 'TV'
            thisArticle.subtitle = ""

            #log(5, funcName, "checking len(moreInfoURL):", len(thisArticle.moreInfoURL))
            if thisArticle.moreInfoURL:
              log(5, funcName, "think we have a meaningful URL:'" + thisArticle.moreInfoURL + "' Count of 'episodes':", thisArticle.moreInfoURL.count("episodes"))
              if thisArticle.moreInfoURL.count("episodes") > 0  or thisArticle.moreInfoURL.count("search.php?search=") > 0: #don't mess with whole season dvd rips
                log(4, funcName, 'found more than 0 episodes in the url:', thisArticle.moreInfoURL)
                tv_metadata = tvrage(thisArticle.moreInfoURL)
                if tv_metadata:
                  thisArticle.metadata = tv_metadata.metadata
                  oldTitle = thisArticle.title
                  if tv_metadata.title != "" :
                    thisArticle.title = tv_metadata.title
                  #thisArticle.description = "Size: " + thisArticle.size + "\n\n" + tv_metadata.summary
                  thisArticle.description = tv_metadata.summary
                  if thisArticle.title != oldTitle:
                    thisArticle.description = "Original Title: " + oldTitle + "\n\n" + thisArticle.description
                  thisArticle.subtitle = "S" + tv_metadata.season + "E" + tv_metadata.episode + " (" + tv_metadata.air_date + ")"
                  if not Client.Platform in ["MacOSX", "Windows"]:
                    thisArticle.description = thisArticle.subtitle + "\n\n" + thisArticle.description
                  thisArticle.rating = tv_metadata.votes
                  if tv_metadata.thumb:
                    thisArticle.thumb = tv_metadata.thumb
                  else:
                    thisArticle.thumb = R('no_thumbnail_tv.png')
                  thisArticle.duration = tv_metadata.duration
              else:
                log(4, funcName, 'Did not find keyword "episodes" or "search.php" in', thisArticle.moreInfoURL, 'for:', thisArticle.title)
            else:
              log(5, funcName, 'No TVRageURL found for:', thisArticle.title)

            # Add the item to the persistent-ish cache
            nzbItems[thisArticle.nzbID] = thisArticle
            
          else: # The nzbID is already in the dict, therefore we can just pull it from cache
            log(4, funcName, "Cached: Adding \"" + nzbItems[thisArticle.nzbID].title + "\" from the cache.")
            thisArticle = nzbItems[thisArticle.nzbID]
          
          log(4, funcName, "Adding \"" + thisArticle.title + "\" to the dir")
          dir.Append(DirectoryItem(Route(Article, theArticleID=thisArticle.nzbID), title=thisArticle.title, subtitle=thisArticle.subtitle, summary=thisArticle.attributes_and_summary, duration=thisArticle.duration, thumb=thisArticle.thumb, rating=thisArticle.rating, infoLabel=thisArticle.size,contextMenu=media_context_menu(itemID=thisArticle.nzbID, existingMenu=cm), air_release_date=get_metadata_date(thisArticle), contextKey=thisArticle.nzbID, contextArgs={}))

        # Now handle the case where we want to consolidate dupes and we have more than one entry.
        # Note that we are still only returning some number of results in a single query to newzbin
        # and we could end up with duplicates across pages... that case is not handled (yet?)
        elif (consolidateDuplicates) and (thisArticle.title in listOfDupes) and (not allOneTitle):
          countOfEntries = countEntries(thisArticle.title, allEntries)
          log(4, funcName, thisArticle.title, "is a duplicate with", countOfEntries, "occurrences.")

          # OK, we'll build a new query with all the dupes
          numEntries = str(countOfEntries) + " Entries"
          dir.Append(Function(DirectoryItem(SearchTV, title=thisArticle.title, infoLabel=numEntries), value=thisArticle.title, title2=thisArticle.title, days=days, maxResults=maxResults, allOneTitle=True))
          listOfDupes.remove(thisArticle.title)
          #lenOfDir+=1

  #if saveDict:
    #log(4, funcName, 'Saving Dict:', nzbItemsDict)
    #Dict[nzbItemsDict] = nzbItems
    #pass
  #dir.nocache=1

  if sort_by == 'NAME': dir.Sort('title')
  if sort_by == 'DATE': dir.Sort('air_release_date', descending=True)

  # We only get back so many results in our request.  If we hit that limit, let's assume there's more behind these
  # results and offer the user the option to go to the next page of results.  
  if (len(allEntries))>=app.nzb.RESULTS_PER_PAGE:
    log(4, funcName + "len(allEntries): ", len(allEntries), " adding an option to go to the next page")
    resultsSoFar = page * app.nzb.RESULTS_PER_PAGE
    page+=1
    log(4, funcName, 'Page being sent to next page:', page)
    dir.Append(Function(DirectoryItem(SearchTV, "More than " + str(resultsSoFar) + " matches, Next Page"), value=value, title2=title2, maxResults=str(app.nzb.RESULTS_PER_PAGE), days=str(days), offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, sort_by=sort_by))
  else:
    log(4, funcName, "Only", len(dir)+dupesFound, "entries found")

  if offerExpanded:
    dir.Append(Function(DirectoryItem(SearchTV, "[Expand this search...]"), value=value, title2="[expanded] " + title2,  maxResults=str(int(maxResults)*ExpandedSearchMaxResultsFactor), days=str(int(days)*ExpandedSearchTimeFactor), offerExpanded=True, expandedSearch=True, page=page, invertVideoQuality=invertVideoQuality))

  # If the user chooses to want to see options outside of their video quality settings, allow them to re-search with inverted quality options
  #if Prefs.Get("OfferAlternateVideoQuality"):
  #  dir.Append(Function(DirectoryItem(SearchTV, "Try searching for other video quality options"), value=value, title2=title2, days=days, invertVideoQuality=True))

  return dir

####################################################################################################
@route(routeBase + 'Article/{theArticleID}')
def Article(theArticleID='', theArticle='nothing', title2='', dirname='', subtitle='', thumb='', fanart='', rating='', summary='', duration=''):
  funcName="[Article]"
  
  if theArticle=='nothing' and not theArticleID=='':
    try:
      nzbItems = Dict[nzbItemsDict]
      theArticle=nzbItems[theArticleID]
    except KeyError:
      x = app.queue.getItem(theArticleID)
      if x:
        theArticle = x.report
      else:
        return Message("No Article", "No Article Found")
    
  
  #Determine what you want to show as the secondary window title
  if theArticle.mediaType=='TV':
    log(9, funcName, theArticle.title, "is a TV show")
    title2 = "TV > " + theArticle.title
  elif theArticle.mediaType=='Movie':
    log(9, funcName, theArticle.title, "is a Movie")
    title2 = "Movies > " + theArticle.title
  else:
    log(3, funcName, theArticle.title, "is an unknown media type (i.e. not a TV show nor a movie")
    title2 = theArticle.title
  
  cm = ContextMenu(includeStandardItems=False)
  #cm.Append(Function(DirectoryItem(context_menu_RemoveItem, title=L('CANCEL_DL'))))
  dir = MediaContainer(viewGroup='Details', title2=title2, noCache=True, noHistory=False, autoRefresh=1, contextMenu=cm, replaceParent=False)
  more_options = False
  
  try:
    if theArticle.fanart != "":
      dir.art = theArticle.fanart
  except:
    pass
  
  #art = Function(DirectoryItem(StupidUselessFunction, subtitle=theArticle.subtitle))
  if app.queue.getItem(theArticle.nzbID) == False:
    #dir.Append(Function(DirectoryItem(StupidUselessFunction, title=theArticle.title, summary=theArticle.summary, thumb=theArticle.thumb, subtitle=theArticle.subtitle), key="a"))
    dir.Append(DirectoryItem(Route(AddReportToQueue, nzbID=theArticle.nzbID), title=L('ITM_QUEUE'), thumb=theArticle.thumb, subtitle=theArticle.title, summary=theArticle.attributes_and_summary, contextKey=theArticle.nzbID, contextArgs={}))

  #########################################################################
  # Pausing is causing problems.
  # Commenting this out but not removing it so we can re-enable it
  # someday.
  #
  #if app.downloader.notPaused:
  #  dir.Append(DirectoryItem(Route(pauseDownload), title=L('Q_PAUSE'), subtitle="Temporarily suspend all downloads", summary="", thumb=R('pause_red.png')))
  #else:
  #  dir.Append(DirectoryItem(Route(resumeDownload), title=L('Q_RESUME'), subtitle="You temporarily suspended downloads.  Resume them now.", summary="", thumb=R('pause_green.png')))
  #########################################################################
  if app.queue.getItem(theArticle.nzbID) != False:
    #log(1, funcName, 'item states:\nitem.downloading:', item.downloading, '\nitem.failing:', item.failing,'\nitem.complete:', item.complete, '\nitem.recoverable:', item.recoverable, '\nitem.recovery_complete:', item.recovery_complete, '\nitem.repair_percent:', item.repair_percent, '\nitem.failed_articles:', len(item.failed_articles))

    item = app.queue.getItem(theArticle.nzbID)
    log(9, funcName, 'item states:\nitem.downloading:', item.downloading, '\nitem.failing:', item.failing, '\nitem.downloadComplete:', item.downloadComplete, '\nitem.complete:', item.complete, '\nitem.recoverable:', item.recoverable, '\nitem.recovery_complete:', item.recovery_complete, '\nitem.repair_percent:', item.repair_percent, '\nitem.failed_articles:', len(item.failed_articles))

    dir.Append(Function(DirectoryItem(StupidUselessFunction, title=theArticle.title, summary=theArticle.attributes_and_summary, thumb=theArticle.thumb, subtitle=theArticle.subtitle, contextKey=item.id, contextArgs={}), key="a"))
    
    #Weird case
#    if item.downloading and item.complete and not item.downloadComplete:
#      item.downloading = False
#      item.downloadComplete = True
#      item.save()

    if item.downloading:
      # One way to display all text if an item is still downloading
      overall_progress = progressText(item)
      cm.Append(Function(DirectoryItem(context_menu_RemoveItem, title=L('CANCEL_DL'))))
      if item.play_ready and not item.failing:
        dir.Append(VideoItem(Route(StartStreamAction, id=item.id), title=L('DL_PLAY_DL'), subtitle=theArticle.subtitle, thumb=R('play_yellow.png'), infoLabel=(('%.1f' % item.percent_complete)+'%'), summary=(overall_progress + '\n' + theArticle.summary), contextKey=item.id, contextArgs={}))
      elif not item.play_ready and not item.failing:
        dir.Append(DirectoryItem(Route(StupidUselessFunction, key="a"), title=(L('DL_DOWNLOADING_PLAY') + L('DL_RTP') + TimeText(item.play_ready_time)), thumb=R('download_green.png'), subtitle="Downloading enough to start playing", infoLabel=(('%.1f' % item.play_ready_percent)+'%'), summary=(overall_progress + '\n' + theArticle.summary), contextKey=item.id, contextArgs={}))
      elif item.failing: #item.failing==True
        dir.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title=L('DL_DAMAGED'), thumb=R('download_green.png'), subtitle="Damaged files, can't play", infoLabel=(('%.1f' % item.percent_complete)+'%'), summary=(overall_progress + '\n' + theArticle.summary), contextKey=item.id, contextArgs={}))
      # Cancel download option - Removed due to Play button stupidity.  Moved to context items.
      #dir.Append(DirectoryItem(Route(CancelDownloadAction, id=item.id), title=L('CANCEL_DL'), thumb=R('trashcan.png'), subtitle='Cancel and delete progress', contextKey=item.id, contextArgs={}))
      #cm.Append(DirectoryItem(Route(context_menu_CancelDownload, id=item.id), title=L('CANCEL_DL'), contextKey=item.id, contextArgs={}))
      more_options = True
    elif item.downloadComplete:
      #Item has finished downloading and saving files to disk
      
      if item.complete:
        #Show options to play and remove the file
        dir.Append(VideoItem(Route(StartStreamAction, id=item.id), title=L('PLAY_DL'), thumb=R('play_green.png'), contextKey=item.id, contextArgs={}))
        cm.Append(Function(DirectoryItem(context_menu_RemoveItem, title=L('REMOVE_DL'))))
      if item.failing:
        
        # Show recovery status (hopefully)
        if not item.recoverable and item.recovery_complete:
          # The file is not recoverable
          dir.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title=L('DL_NOT_RECOVERABLE'), thumb=R('thumbs-down.png'), subtitle="Files damaged beyond repair", contextKey=item.id, contextArgs={}))
          cm.Append(Function(DirectoryItem(context_menu_RemoveItem, title=L('REMOVE_DL'))))
          more_options = True
        elif item.currently_recovering:
          if item.repair_percent == 0:
            # Still evaluating recoverability
            dir.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title=L('DL_RECOVERING'), thumb=R('analyzing.png'), subtitle='Analyzing file for recoverability', contextKey=item.id, contextArgs={}))
          else:
            # Recovery is in progress
            dir.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title=F('DL_RECOVERING_PCT', (str(item.repair_percent)+'%')), thumb=R('thumbs-up.png'), subtitle='Repairing files', contextKey=item.id, contextArgs={}))
        
        elif item.currently_unpacking:
          # The item is being unpacked
          dir.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title='Extracting media file', subtitle='Extracting media file', contextKey=item.id, contextArgs={}))
        
        else:# not item.currently_recovering and not item.currently_unpacking:
          cm.Append(Function(DirectoryItem(context_menu_RemoveItem, title=L('REMOVE_DL'))))
          # Need to show the recover and extract buttons
          if not item.recovery_complete:
            # We need to try recover the item
            dir.Append(DirectoryItem(Route(Recover, nzbID=item.id), title="Recover", contextKey=item.id, contextArgs={}))
            #dir.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title='Starting Recovery'))
            #Recover(item.id)
          else:
            # Let the item be unpacked
            if item.recoverable:
              dir.Append(DirectoryItem(Route(Unpack, nzbID=item.id), title='Extract media file', subtitle='Media file needs to be extracted', contextKey=item.id, contextArgs={}))
              #dir.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title='Starting media extraction'))
              #Unpack(item.id)
      #dir.Append(DirectoryItem(Route(RemoveItemAction, id=item.id), title=L('REMOVE_DL'), thumb=R('trashcan.png'), contextKey=item.id, contextArgs={}))
      more_options = True

    else: #Must be queued for downloading
      dir.Append(DirectoryItem(Route(StupidUselessFunction, key="a"), title=L('DL_QUEUED'), thumb=R('download_green.png'), subtitle="Download queued", summary=theArticle.attributes_and_summary, contextKey=item.id, contextArgs={}))
      cm.Append(Function(DirectoryItem(context_menu_RemoveItem, title=L('CANCEL_DL'))))
      more_options = True
    #dir.Append(DirectoryItem(Route(CancelDownloadAction, id=item.id), title=L('CANCEL_DL'), thumb=R('trashcan.png'), contextKey=item.id, contextArgs={}))
      
    #Show the option to delete the item
  
#  if more_options:
#    dir.Append(PopupDirectoryItem(Route(item_more_options, id=item.id), title='Cancel and/or Delete'))
#  if len(app.queue.downloadableItems) >= 1:
#    dir.Append(DirectoryItem(Route(manageQueue), title=("View Download Queue (" + str(len(app.queue.downloadableItems)) + " items)"), thumb=R('download_queue.png')))
#  if len(app.queue.completedItems) >= 1:
#    dir.Append(DirectoryItem(Route(manageCompleteQueue), title=("View Completed Queue (" + str(len(app.queue.completedItems)) + " items)"), thumb=R('check_green.png')))

  #dir.Append(addToQueue)
  if len(cm) == 0: cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
  #log(1, funcName, 'len(cm):', len(cm))
  return dir

####################################################################################################
def media_context_menu(item=None, itemID=None, existingMenu=None):
  funcName = '[media_context_menu]'
  
  # If the item already has an existing contextual menu, use it as a starting point.
  cm = ContextMenu(includeStandardItems=False)
  if existingMenu:
    for thing in existingMenu:
      cm.Append(thing)
  
  # If there's only an itemID, go get the actual item
  if not item and itemID:
    log(5, funcName, 'Getting item with id:', itemID)
    item = app.queue.getItem(itemID)
  if item:
    log(5, funcName, item.report.title, ': Got this item:', item)
    if item.play_ready and not item.complete:
      log(5, funcName, item.report.title, ': Giving you a CANCEL context menu')
      cm.Append(Function(DirectoryItem(context_menu_RemoveItem, title=L('CANCEL_DL'))))
      #cm.Append(DirectoryItem(Route(context_menu_RemoveItem), title=L('CANCEL_DL')))
    elif item.complete:
      log(5, funcName, item.report.title, ': Giving you a REMOVE context menu')
      cm.Append(Function(DirectoryItem(context_menu_RemoveItem, title=L('REMOVE_DL'))))
      #cm.Append(DirectoryItem(Route(context_menu_RemoveItem), title=L('REMOVE_DL')))
    else:
      if len(cm) < 1: log(5, funcName, item.report.title, ': Giving you a NO OPTIONS context menu')
      cm.Append(Function(DirectoryItem(StupidUselessFunction, title=('No Options')), key='a'))      
      #cm.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title="No Options"))
  else:
    log(5, funcName, itemID, ': Defaulting to no options context menu')
    if len(cm) < 1: cm.Append(Function(DirectoryItem(StupidUselessFunction, title=('No Options')), key='a'))      
    #cm.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title="No Options"))
  return cm
####################################################################################################
def progressText(item):
  funcName = '[progressText]'
  global app
  overall_progress = ''
  if item.downloading:
    #If it's ready to play, give the user the option here
    #log(8, funcName, 'progress')
    progress = 'Progress: ' + (('%.1f' % item.percent_complete) + '%')
    #log(8, funcName, 'speed')
    try:
      speed = 'Latest Speed: ' + str(convert_bytes(app.nntpManager.speed)) + '\nAverage Speed: ' + str(convert_bytes(item.speed))
      progress_speed = progress + '\n' + speed
    except:
      log(1, funcName, 'Could not calculate speed:', sys.exc_info()[1])
      progress_speed = progress
    #log(8, funcName, 'Ready to play')
    rtp = 'Ready to play: ' + (('%.1f' % item.play_ready_percent) + '%')
    if item.failing:
      if len(item.failed_articles) <= (item.nzb.total_recovery_blocks * .85):
        damage = "***" + L('DL_DAMAGE_RECOVERY_NOTICE') + "***" + '\n'
      else:
        damage = '!!!\n' + F('DL_DAMAGE_WARNING', len(item.failed_articles), item.nzb.total_recovery_blocks) + '\n!!!\n'
    
    rtp_progress_speed = rtp + '\n' + progress_speed
    #log(7, funcName, 'incoming files:', len(item.incoming_files), 'nzb rars:', len(item.nzb.rars))
    #log(8, funcName, 'rar progress')
    rar_progress = F('DL_RAR_PROGRESS', len(item.incoming_files), len(item.nzb.rars))
    
    if Prefs['ShowRARProgress']:
      if item.play_ready and not item.failing:
        overall_progress = rar_progress + '\n' + progress_speed
      elif item.failing:
        overall_progress = damage + '\n' + rar_progress + '\n' + progress_speed
      elif not item.play_ready and not item.failing:
        overall_progress = rar_progress + '\n' + rtp_progress_speed
    else:
      if item.play_ready and not item.failing:
        overall_progress = progress_speed
      elif item.failing:
        overall_progress = damage + '\n' + progress_speed
      elif not item.play_ready and not item.failing:
        overall_progress = rtp_progress_speed
      #overall_progress = rtp_progress_speed
  #log(7, funcName, 'overall progress:', overall_progress)
  return overall_progress

####################################################################################################
@route(routeBase + 'Recover/{nzbID}')
def Recover(nzbID):
  item = app.queue.getItem(nzbID)
  item.recover_par()

@route(routeBase + 'Unpack/{nzbID}')
def Unpack(nzbID):
  item = app.queue.getItem(nzbID)
  item.unpack(item.nzb.rars[0].name)
####################################################################################################
@route(routeBase + 'AddReportToQueue/{nzbID}')
def AddReportToQueue(nzbID, article='nothing'):
  funcName = "[AddReportToQueue]"
  global app
  log(5, funcName, 'Setting queue object, should be using previously initialized app object''s queue')
  queue = app.queue
  log(5, funcName, 'queue object set')
  if article=='nothing':
    nzbItems = Dict[nzbItemsDict]
    article = nzbItems[nzbID]
  #item = queue.add(nzbID, nzb, article)
  queue.add(nzbID, app.nzb, article)
  #item.download()
  #log(5, funcName, 'Items queued:', len(app.queue.items))
  header = 'Item queued'
  message = '"%s"\nhas been added to your queue' % article.title #item.report.title
  return Message(header, message)

####################################################################################################
@route(routeBase + 'manageCompleteQueue')
def manageCompleteQueue(key=None, sender=None, media_type_filter=None, sort_by=None, filter=None, **kwargs):
  funcName = "[manageCompleteQueue]"
  FileSystem = FS()

  # Some cleanup to avoid errors
  #if app.stream_initiator != None: app.stream_initiator = None
  dir_replace_parent = False
  cm = ContextMenu(includeStandardItems=False)
  if sort_by == None:
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SORT_NAME')), media_type_filter=media_type_filter, sort_by='NAME', filter=filter))
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SORT_DATE')), media_type_filter=media_type_filter, sort_by='DATE', filter=filter))
  elif sort_by == 'NAME':
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SORT_UNSORTED')), media_type_filter=media_type_filter, sort_by=None, filter=filter))
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SORT_DATE')), media_type_filter=media_type_filter, sort_by='DATE', filter=filter))
    dir_replace_parent = True
  elif sort_by == 'DATE':
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SORT_UNSORTED')), media_type_filter=media_type_filter, sort_by=None, filter=filter))
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SORT_NAME')), media_type_filter=media_type_filter, sort_by='NAME', filter=filter))
    dir_replace_parent = True
  
  if media_type_filter == None:
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SHOW_ONLY_MOVIES')), media_type_filter='MOVIE', sort_by=sort_by, filter=filter))
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SHOW_ONLY_TV')), media_type_filter='TV', sort_by=sort_by, filter=filter))
  elif media_type_filter == 'MOVIE':
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SHOW_ALL')), media_type_filter=None, sort_by=sort_by, filter=filter))
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SHOW_ONLY_TV')), media_type_filter='TV', sort_by=sort_by, filter=filter))
    dir_replace_parent = True
  elif media_type_filter == 'TV':
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SHOW_ALL')), media_type_filter=None, sort_by=sort_by, filter=filter))
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SHOW_ONLY_MOVIES')), media_type_filter='MOVIE', sort_by=sort_by, filter=filter))
    dir_replace_parent = True
  elif media_type_filter == 'SERIES':
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SHOW_ALL')), media_type_filter=None, sort_by=sort_by, filter=filter))
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SHOW_ONLY_MOVIES')), media_type_filter='MOVIE', sort_by=sort_by, filter=filter))
    cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SHOW_ONLY_TV')), media_type_filter='TV', sort_by=sort_by, filter=filter))
    dir_replace_parent = True
    
    
  noun = 'Completed'
  if filter != None:
    if filter == 'Archived': noun = 'Archived'
    
  dir = MediaContainer(viewGroup="Details", title2=(noun + " Items"), replaceParent=dir_replace_parent, noCache=True, autoRefresh=30, contextMenu=cm)
  #dir = ObjectContainer(view_group="Details", title2=(noun + " Items"), no_cache=True, replace_parent=dir_replace_parent)#, auto_refresh=30, context_menu=cm)
  
  if len(app.queue.completedItems) > 0:
    for item in app.queue.completedItems:
      #Weird case
      if item.downloading and item.complete:
        log(1, funcName, 'Fixing item with item.downloading == True and item.complete == True:', item.report.title)
        item.downloading = False
        item.downloadComplete = True
        item.save()
      #dir.Append(Function(DirectoryItem(Article, title=item.report.title, subtitle=item.report.subtitle, summary=item.report.attributes_and_summary, contextKey=item.id, contextArgs={}), theArticleID=item.id))

      
      item_cm = ContextMenu(includeStandardItems=False)
      item_cm.Extend(cm)
      cm_archive = False
      cm_archive_delete = False
      cm_remove = False
      cm_archive_again = False
      cm_archiving = False
      
      if item.downloading==False and item.complete==False and item.downloadComplete==True and item.failing==False:
        log(1, funcName, 'fixing item with "item.downloading==False and item.complete==False and item.downloadComplete==True and item.failing==False":', item.report.title)
        item.complete = True
        item.save()
      if item.complete:

        if media_type_filter == None or (media_type_filter.lower() == item.report.mediaType.lower()): 

          #Check the archived filter first
          if filter != None:
            if filter=="Archived" and hasattr(item, 'archived'):
              if item.archived:
                pass # basically continue
              else:
                # item is not archived, don't add it to the dir
                continue
            else:
              # item doesn't have the archive attribute, don't add it to the dir
              continue

          if item.report.subtitle:
            subtitle = item.report.subtitle
          else:
            subtitle = item.report.reportAge
          if not hasattr(item.report, "metadata"):
            log(1, funcName, 'No metadata:', item.report.title, ', URL:', item.report.moreInfoURL, ', or ID:', item.report.moreInfo)
            continue
#          if item.report.mediaType == "TV" and media_type_filter != "SERIES":
#            item_cm.Append(Function(DirectoryItem(manageCompleteQueue, title=L('SHOW_ONLY_SERIES')), media_type_filter='TV', sort_by=sort_by))
          
          #Determine what to show re: archiving
          if not hasattr(item, 'archiving'): #if the archiving attribute doesn't exist, it's probably a good bet the archived attributed doesn't exist.
            if (item.report.mediaType == 'TV' and getConfigValue(FSConfigDict, TV_ARCHIVE_FOLDER) and FileSystem.folder_available(getConfigValue(FSConfigDict, TV_ARCHIVE_FOLDER))) or (item.report.mediaType == 'Movie' and getConfigValue(FSConfigDict, MOVIE_ARCHIVE_FOLDER) and FileSystem.folder_available(getConfigValue(FSConfigDict, MOVIE_ARCHIVE_FOLDER))):
              if Core.storage.file_exists(item.fullPathToMediaFile):
                cm_archive = True
                cm_archive_delete = True
              cm_remove = True
          else:
            if not item.archiving:
              if (item.report.mediaType == 'TV' and getConfigValue(FSConfigDict, TV_ARCHIVE_FOLDER) and FileSystem.folder_available(getConfigValue(FSConfigDict, TV_ARCHIVE_FOLDER))) or (item.report.mediaType == 'Movie' and getConfigValue(FSConfigDict, MOVIE_ARCHIVE_FOLDER) and FileSystem.folder_available(getConfigValue(FSConfigDict, MOVIE_ARCHIVE_FOLDER))):
                if not hasattr(item, 'archived'):
                  if Core.storage.file_exists(item.fullPathToMediaFile):
                    cm_archive = True
                    cm_archive_delete = True
                else:
                  if item.archived:
                    if Core.storage.file_exists(item.fullPathToMediaFile):
                      cm_archive_again = True
                      cm_archive_delete = True
                  else:
                    if Core.storage.file_exists(item.fullPathToMediaFile):
                      cm_archive = True
                      cm_archive_delete = True
                cm_remove = True
            else:
              cm_archiving = True
          
          # Add all the context menu items
          if cm_archive: item_cm.Append(Function(DirectoryItem(archiveItem, title=L('ARCHIVE_ITEM')), itemID=item.id))
          if cm_archive_again: item_cm.Append(Function(DirectoryItem(archiveItem, title=L('ARCHIVE_ITEM_AGAIN')), itemID=item.id))
          if cm_archive_delete: item_cm.Append(Function(DirectoryItem(archiveItem, title=L('ARCHIVE_DELETE_ITEM')), itemID=item.id, delete=True))
          if cm_remove: item_cm.Append(Function(DirectoryItem(context_menu_RemoveItem, title=L('REMOVE_DL'))))
          if cm_archiving: item_cm.Append(Function(DirectoryItem(StupidUselessFunction, title=L('ARCHIVING')), key='a'))
          item_cm.Append(Function(DirectoryItem(SearchSubtitles, title='Download Subtitles (eng)'), itemID=item.id, file=item.fullPathToMediaFile, size=item.files[item.mediaFileName]))

          if Core.storage.file_exists(item.fullPathToMediaFile):
            dir.Append(VideoItem(Route(StartStreamAction, id=item.id), title=item.report.title, thumb=R('play_green.png'), subtitle=subtitle, summary=item.report.attributes_and_summary, contextMenu=item_cm, contextKey=item.id, air_release_date=get_metadata_date(item), contextArgs={}))
            #dir.add(MediaObject(parts=[PartObject(StartStreamAction(id=item.id))], 
          else:
            dir.Append(DirectoryItem(Route(Message, title="File Error", message="Media File Not Found"), title=item.report.title, subtitle=item.report.subtitle, summary=item.report.attributes_and_summary, contextMenu=item_cm, contextKey=item.id, contextArgs={}))
      else:
        log(1, funcName, 'Adding incomplete item:', item.report.title)
        dir.Append(DirectoryItem(Route(Article, theArticleID=item.id), title=item.report.title, subtitle=item.report.subtitle, summary=item.report.attributes_and_summary, contextKey=item.id, contextArgs={}))
  if len(dir) == 0:
    dir.add(DirectoryItem(Route(StupidUselessFunction, key='a'), title=("No " + noun + " Downloads"), subtitle=("There are no " + noun.lower() + " items to display"), summary="", contextKey='a', contextArgs={}))   
  if sort_by == 'NAME': dir.Sort('title')
  if sort_by == 'DATE': dir.Sort('air_release_date', descending=True)

  return dir
####################################################################################################
@route(routeBase + 'archiveItem')
def archiveItem(sender=None, key=None, itemID=None, delete=False):
  funcName = '[archiveItem]'
  if not itemID:
    return Message('Error', 'No item to archive')
  
  item = app.queue.getItem(itemID)
  if not item:
    return Message('Error', 'Could not retrieve item')
    
  Thread.Create(item.archive, item, delete=delete)

####################################################################################################
@route(routeBase + 'viewArchivingItems')
def viewArchivingItems(key=None, sender=None):
  funcName = '[viewArchivingItems]'
  log(7, funcName, 'Items in archive queue:', len(app.queue.archivingItems))
  cm = ContextMenu(includeStandardItems=False)
  dir = MediaContainer(viewGroup="Details", title2="Archiving Items", nocache=True, autoRefresh=5, contextMenu=cm)
  if len(app.queue.archivingItems) > 0:
    for item in app.queue.archivingItems:
      dir.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title=item.report.title, subtitle=item.report.subtitle, summary=item.report.attributes_and_summary, contextMenu=cm, contextKey=item.id, contextArgs={}))
  else:
    dir.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title='Nothing being archived', contextMenu=cm, contextKey='a', contextArgs={}))
  return dir
  
####################################################################################################
@route(routeBase + 'manageQueue')
def manageQueue(key=None, sender=None, media_type_filter=None, sort_by=None):
  funcName = "[manageQueue]"
  download_queue_filterable = False
  # First check if there's anything in the queue
  log(7, funcName, 'Items in download queue:', len(app.queue.downloadableItems))
    
  # Display the contents of the queue
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(context_menu_RemoveItem, title=L('REMOVE_DL'))))
  if download_queue_filterable:
    if media_type_filter == None:
      cm.Append(Function(DirectoryItem(manageQueue, title=L('SHOW_ONLY_MOVIES')), media_type_filter='MOVIE', sort_by=sort_by))
      cm.Append(Function(DirectoryItem(manageQueue, title=L('SHOW_ONLY_TV')), media_type_filter='TV', sort_by=sort_by))
    elif media_type_filter == 'MOVIE':
      cm.Append(Function(DirectoryItem(manageQueue, title=L('SHOW_ALL')), media_type_filter=None, sort_by=sort_by))
      cm.Append(Function(DirectoryItem(manageQueue, title=L('SHOW_ONLY_TV')), media_type_filter='TV', sort_by=sort_by))
    elif media_type_filter == 'TV':
      cm.Append(Function(DirectoryItem(manageQueue, title=L('SHOW_ALL')), media_type_filter=None, sort_by=sort_by))
      cm.Append(Function(DirectoryItem(manageQueue, title=L('SHOW_ONLY_MOVIES')), media_type_filter='MOVIE', sort_by=sort_by))
  
  log(7, funcName, 'Creating dir')
  dir = MediaContainer(viewGroup="Details", title2="Queued Items", noCache=True, autoRefresh=1, contextMenu=cm)
  ############################################################
  # Pausing is causing problems.  Commenting it out in
  # hope of fixing it one day
  #
  #if app.downloader.notPaused:
  #  dir.Append(DirectoryItem(Route(pauseDownload), title="Pause Downloading", subtitle="Temporarily suspend all downloads", summary=""))
  #else:
  #  dir.Append(DirectoryItem(Route(resumeDownload), title="Resume Downloading", subtitle="You temporarily suspended downloads.  Resume them now.", summary=""))
  #############################################################
  
  log(7, funcName, 'Looking at each item in queue')
  for item in app.queue.downloadableItems:
    # if this item should be filtered out, just skip it now
    if download_queue_filterable and not (media_type_filter == None or media_type_filter.lower() == item.report.mediaType.lower()): continue
    #Weird case
#    if item.downloading and item.complete and not item.downloadComplete:
#      item.downloading = False
#      item.downloadComplete = True
#      item.save()
#      continue
    
    log(7, funcName, 'Examining:', item.report.title, 'at overall index:', app.queue.items.index(item.id), 'and relative index:', app.queue.downloadableItems.index(item))
    subtitle = ' '
    summary = ' '
    overall_progress = progressText(item)
    
    # Build out the item's contextual menu options
    item_cm = ContextMenu(includeStandardItems=False)
    item_cm.Extend(cm)
    download_index = app.queue.downloadableItems.index(item)
    overall_index = app.queue.items.index(item.id)
    bottom_of_queue_index = app.queue.items.index(app.queue.downloadableItems[len(app.queue.downloadableItems)-1].id)
    top_of_queue_index = app.queue.items.index(app.queue.downloadableItems[0].id)
    
    log(7, funcName, 'length of download queue:', len(app.queue.downloadableItems))
    if len(app.queue.downloadableItems) > 1:
      if download_index == 0:
        # First in the download queue
        if len(app.queue.downloadableItems) > 2:
          item_cm.Append(Function(DirectoryItem(move_queued_item, title=L('QUEUE_MOVE_DOWN')), old_index=overall_index, new_index=overall_index+1, reset=True))
        item_cm.Append(Function(DirectoryItem(move_queued_item, title=L('QUEUE_MOVE_BOTTOM')), old_index=overall_index, new_index=(bottom_of_queue_index+2), reset=True))
      elif download_index == 1 and download_index != (len(app.queue.downloadableItems)-1):
        # Second in queue, no need for "move to top"
        item_cm.Append(Function(DirectoryItem(move_queued_item, title=L('QUEUE_MOVE_UP')), old_index=overall_index, new_index=overall_index-1, reset=True))
        item_cm.Append(Function(DirectoryItem(move_queued_item, title=L('QUEUE_MOVE_DOWN')), old_index=overall_index, new_index=overall_index+1))
        item_cm.Append(Function(DirectoryItem(move_queued_item, title=L('QUEUE_MOVE_BOTTOM')), old_index=overall_index, new_index=(bottom_of_queue_index+2)))
      elif download_index > 1 and download_index != (len(app.queue.downloadableItems)-1):
        # Anywhere in the middle of the queue
        if len(app.queue.downloadableItems) > 3:
          item_cm.Append(Function(DirectoryItem(move_queued_item, title=L('QUEUE_MOVE_UP')), old_index=overall_index, new_index=overall_index-1))
        item_cm.Append(Function(DirectoryItem(move_queued_item, title=L('QUEUE_MOVE_TOP')), old_index=overall_index, new_index=top_of_queue_index, reset=True))
        if len(app.queue.downloadableItems) > 3:
          item_cm.Append(Function(DirectoryItem(move_queued_item, title=L('QUEUE_MOVE_DOWN')), old_index=overall_index, new_index=overall_index+1))
        item_cm.Append(Function(DirectoryItem(move_queued_item, title=L('QUEUE_MOVE_BOTTOM')), old_index=overall_index, new_index=(bottom_of_queue_index+2)))
      elif download_index == (len(app.queue.downloadableItems)-1):
        # Last item in the queue
        if len(app.queue.downloadableItems) > 2:
          item_cm.Append(Function(DirectoryItem(move_queued_item, title=L('QUEUE_MOVE_UP')), old_index=overall_index, new_index=overall_index-1))
        item_cm.Append(Function(DirectoryItem(move_queued_item, title=L('QUEUE_MOVE_TOP')), old_index=overall_index, new_index=top_of_queue_index, reset=True))
        
    if item.play_ready and not item.failing:
      log(7, funcName, 'item.play_ready:', item.play_ready)
      subtitle = L('DL_PLAY_READY')      
      summary = overall_progress
    elif item.failing:
      subtitle = L('DL_DAMAGED')
      summary = overall_progress
    elif item.downloading and not item.failing:
      log(7, funcName, 'item.downloading:', item.downloading)
      log(7, funcName, 'item.play_ready_time:', item.play_ready_time)
      
      # All these strings can be found in the Strings folder of the bundle
      tm = item.play_ready_time
      if tm == 0:
        subtitle = L('DL_PLAY_READY')
        summary = overall_progress
      else:
        ttp = TimeText(tm)
        summary = L('DL_RTP') + ttp + "\n" + overall_progress

    else:
      subtitle = L('DL_QUEUED')
      #summary = item.report.summary
    summary += "\n" + item.report.summary
    log(8, funcName, 'Queue item:', item.report.title+': subtitle:', subtitle, 'summary:', summary)
    log(7, funcName, 'Found in queue:', item.report.title)
    
    dir.Append(DirectoryItem(Route(Article, theArticleID=item.id), title=item.report.title, subtitle=subtitle, summary=summary, contextMenu=item_cm, contextKey=item.id, contextArgs={}))

  if len(dir) == 0:
    dir.Append(DirectoryItem(Route(StupidUselessFunction, key=""), title="0 items in download queue", subtitle="Nothing to download", summary="", contextKey='a', contextArgs={}))

  return dir

def move_queued_item(sender=None, key=None, old_index=None, new_index=None, reset=False):
  funcName = '[move_queued_item]'
  moved = False
  if old_index and new_index:
    log(5, funcName, 'Moving item from index', old_index, 'to index', new_index)
    global app
    moved = app.queue.items.move(old_index=old_index, new_index=new_index)
    if moved:
      log(5, funcName, 'Moved successfully!')
    else:
      log(1, funcName, 'Move failed:', sys.exc_info()[1])
  else:
    log(3, funcName, 'Not enough values: old_index:', old_index, 'new_index:', new_index)
  if moved and reset:
    resetDownloader()
  return moved
#####################################################################################################
def TimeText(tm):
  ttp = ''
  if tm < 3:
    ttp = L('DL_SUM_PR_FEW_SECS')
  elif tm > 60:
    mins = tm / 60
    secs = tm % 60
    if mins == 1:
      key = 'DL_SUM_PR_MIN_SECS'
    else:
      key = 'DL_SUM_PR_MINS_SECS'
    ttp = F(key, mins, secs)
  else:
    ttp = F('DL_SUM_PR_SECS', tm)
  return ttp

####################################################################################################
# These functions are related specifically to the queue
####################################################################################################

@route(routeBase + 'queue/{id}/play')
def StartStreamAction(id):
  funcName = "[StartStreamAction]"
  item = app.queue.getItem(id)
  log(6, funcName, "Got id:", item.id)

  if not item: return Message("No Item", "Did not find item")
  if item.play_ready or item.complete:
    return Redirect(item.stream)

@route(routeBase + 'resetDownloader')
def resetDownloader():
  funcName = '[resetDownloader]'
  log(5, funcName, 'Stopping downloader')
  app.downloader.stop_download_thread()
  app.downloader.resetArticleQueue()
  time.sleep(3)
  app.downloader.notPaused = True
  app.downloader.start_download_thread()
  
@route(routeBase + 'pauseDownload')
def pauseDownload():
  funcName = "[pauseDownload]"
  log(5, funcName, "Pausing downloader client tasks")
  app.downloader.stop_download_thread()
  #return True

@route(routeBase + 'resumeDownload')
def resumeDownload():
  funcName = "[resumeDownload]"
  log(5, funcName, "Resuming downloader client tasks")
  app.downloader.restart_download_thread()
  #return True

@route(routeBase + 'queue/{id}/cancel')
def CancelDownloadAction(id):
  funcName = "[CancelDownloadAction]"
  log(5, funcName, "Canceling the download for", id)
  # Get the item so you can remove it from all the queues
  global app
  item = app.queue.getItem(id)
  if item.downloading:
    log(5, funcName, "Pausing the downloader task")
    app.downloader.stop_download_thread()
    app.downloader.resetArticleQueue()
    #while app.downloader.active_clients > 0:
      #log(7, funcName, "waiting for the downloads to stop.")
      #sleep(1)
  # Remove the item from the queue
  app.queue.items.remove(id)
  folderDeleted = item.delete()
  log(7, funcName, 'deleted folder:', folderDeleted)
  # Restart the downloader task
  if item.downloading:
    log(5, funcName, "Restarting download client tasks")
    app.downloader.resetArticleQueue()
    app.downloader.notPaused = True
    app.downloader.start_download_thread()

@route(routeBase + 'queue/{id}/remove')
def RemoveItemAction(id):
  funcName = "[RemoveItemAction]"
  log(5, funcName, "Removing id", id, "from the queue")
  item = app.queue.getItem(id)
  folderDeleted = item.delete()
  log(7, funcName, 'Folder deleted:', folderDeleted)
  if folderDeleted:
    app.queue.items.remove(id)
  else:
    return Message("Error", "Item not deleted: " + str(item))
  
  #return Message("Successfully Deleted", "The item was successfully deleted.")
#  return True

@route(routeBase + 'item_contextual_options/{id}')
def item_contextual_options(id):
  global app
  item = app.queue.getItem(id)
  dir = MediaContainer(title="More Options")
  dir.Append(DirectoryItem(Route(StupidUselessFunction, key='a'), title="Abort!"))
  if item.complete:
    dir.Append(DirectoryItem(Route(RemoveItemAction, id=id), title="Remove"))
  else:
    dir.Append(DirectoryItem(Route(CancelDownloadAction, id=id), title="Cancel and Delete"))
  return dir
    
@route(routeBase + 'context_menu_RemoveItem/')
def context_menu_RemoveItem(sender, key):
  item = app.queue.getItem(key)
  if item.downloadComplete:
    return RemoveItemAction(key)
  else:
    CancelDownloadAction(key)

#@route(routeBase + 'context_menu_CancelDownload/{key}')
#def context_menu_CancelDownload(key):
#  CancelDownloadAction(key)
####################################################################################################
def Search(sender, query, category):
  funcName = "[Search] "
  global app
  SearchList = []
  SearchList.append(query)
  usableQuery = app.nzb.concatSearchList(SearchList)
  usableQuery = query
  #log(7, funcName, 'query:', query, 'category:', category)

  if category == app.nzb.CAT_MOVIES: #movies
    dir = SearchMovies(sender, value=usableQuery, title2=query, days=TVSearchDays_Default, maxResults=str(app.nzb.RESULTS_PER_PAGE), offerExpanded=False)

  elif category == app.nzb.CAT_TV: #tv
    dir = SearchTV(sender, value=usableQuery, title2=query, days=MovieSearchDays_Default, maxResults=str(app.nzb.RESULTS_PER_PAGE), offerExpanded=False)
    
  return dir

####################################################################################################
def BrowseMovieGenres(sender, filterBy):
  funcName = "[BrowseMovieGenres] "
  global app
  # Empty context menu, since there aren't any useful contextual options right now.
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="No Options")))
  dir = MediaContainer(contextMenu=cm, noCache=True, viewGroup='Details', title2='Movies by Genre')

  #next item is the "all genres" item.
  dir.Append(Function(DirectoryItem(SearchMovies, title="All Genres", contextKey="a", contextArgs={}), value='', title2='All Genres', days=MovieSearchDays_Default, maxResults=str(app.nzb.RESULTS_PER_PAGE)))
  try:
    filterHTML = HTTP.Request(app.nzb.SEARCH_URL, cacheTime=MOVIE_GENRE_CACHE_TIME)
    log(9, funcName, 'filterHTML', filterHTML)
    filterXML = HTML.ElementFromString(filterHTML.content)
    genres = filterXML.xpath('//optgroup[@label="' + filterBy + '"]/option')
    for genre in genres:
      title = genre.text.strip() #.encode('utf-8')
      log(4, funcName + "title: " + str(title))
      attrTitle = "a:VideoG~" + title
      dir.Append(Function(DirectoryItem(SearchMovies, title=title, contextKey="a", contextArgs={}), value=attrTitle, title2=title, days=MovieSearchDays_Default, maxResults=str(app.nzb.RESULTS_PER_PAGE)))
  except:
    log(1, funcName, 'Error retreiving genres:', sys.exc_info()[1])
  return dir

####################################################################################################
def BrowseTVGenres(sender, filterBy):
  funcName = "[BrowseTV] "
  global app
  # Empty context menu, since there aren't any useful contextual options right now.
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="No Options")))

  dir = MediaContainer(viewGroup='Details', title2='TV by Genre')
  # next item is the "all genres" item.
  dir.Append(Function(DirectoryItem(SearchTV, title="All Genres"), value="", title2='All Genres', days=TVSearchDays_Default, maxResults=str(app.nzb.RESULTS_PER_PAGE), offerExpanded=False))

  # Get the list of genres from the nzb service
  try:
    filterHTML = HTTP.Request(app.nzb.SEARCH_URL)
    filterXML = HTML.ElementFromString(filterHTML.content)
    genres = filterXML.xpath('//optgroup[@label="' + filterBy + '"]/option')
    # Present each genre in a list
    for genre in genres:
      title = genre.text.strip()
      log(4, funcName + "title: " +str(title))
      # for newzbin, searching by attribute name
      attrTitle = "a:VideoG~" + title
      dir.Append(Function(DirectoryItem(SearchTV, title=title), value=attrTitle, title2=title, days=TVSearchDays_Default, maxResults=str(app.nzb.RESULTS_PER_PAGE), offerExpanded=False))
  except:
    log(1, funcName, 'Error retrieving genres:', sys.exc_info()[1])
  return dir

####################################################################################################
def SearchMovies(sender, value, title2, maxResults=str(0), days=MovieSearchDays_Default, offerExpanded=False, expandedSearch=False, page=1, invertVideoQuality=False, allOneTitle=False, sort_by=None, key=None):
  funcName = "[SearchMovies] "
  global app
  log(4, funcName + "Incoming variables: value:", value, ", title2:", title2, ", maxResults:", maxResults, ", days:", days, ", page:",page)

  # Determine if we will be consolidating duplicates to a single entry
  if allOneTitle:
    consolidateDuplicates = False
  else:
    consolidateDuplicates = bool(Prefs['consolidateMovieDuplicates'])

  #NZB Search functions accept lists
  if isinstance(value, str):
    value = [value]

  #make a meaningful title for the window
  thisTitle = "Movies > "
  if page>1: thisTitle += "Page " + str(page) + " > "
  thisTitle += title2
  
  dir_replace_parent = False
  cm = ContextMenu(includeStandardItems=False)
  if sort_by == None:
    cm.Append(Function(DirectoryItem(SearchMovies, title=L('SORT_NAME')), value=value, title2=title2, maxResults=maxResults, days=days, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by='NAME'))
    cm.Append(Function(DirectoryItem(SearchMovies, title=L('SORT_DATE')), value=value, title2=title2, maxResults=maxResults, days=days, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by='DATE'))
  elif sort_by == 'NAME':
    cm.Append(Function(DirectoryItem(SearchMovies, title=L('SORT_UNSORTED')), value=value, title2=title2, maxResults=maxResults, days=days, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by=None))
    cm.Append(Function(DirectoryItem(SearchMovies, title=L('SORT_DATE')), value=value, title2=title2, maxResults=maxResults, days=days, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by='DATE'))
    dir_replace_parent = True
  elif sort_by == 'DATE':
    cm.Append(Function(DirectoryItem(SearchMovies, title=L('SORT_UNSORTED')), value=value, title2=title2, maxResults=maxResults, days=days, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by=None))
    cm.Append(Function(DirectoryItem(SearchMovies, title=L('SORT_NAME')), value=value, title2=title2, maxResults=maxResults, days=days, offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality, allOneTitle=allOneTitle, sort_by='NAME'))
    dir_replace_parent = True
    
  dir = MediaContainer(viewGroup='Details', title2=thisTitle, noCache=False, replaceParent=dir_replace_parent, contextMenu=cm)
  nzbItems = Dict[nzbItemsDict]
  saveDict = True

  # Go get the data
  allEntries = app.nzb.search(category=app.nzb.CAT_MOVIES, query_list=value, period=app.nzb.calcPeriod(days), page=page)
  if not len(allEntries)>=1:
    return Message(title="No Matching Results", message="Your search did not yield any matches")

  # See if there are dupes, if we are interested in consolidating them
  if consolidateDuplicates:
    dupesFound, listOfUniques, listOfDupes = checkForDupes(allEntries)
    log(4, funcName, "dupesFound:", dupesFound)
    log(4, funcName, "listOfDuplicates:", listOfDupes)
    log(4, funcName, "listOfUniques:", listOfUniques)
  else:
  	dupesFound = 0
  	listOfUniques = []
  	listOfDupes = []

  @parallelize
  def doMovieMetaDataLookups():
    for entry in allEntries:
      @task
      def IterableElement1(thisArticle = entry):
        thisArticle.mediaType = 'Movie'

        # Check to see if this is a duplicate and we should be de-duping
        # First pass will handle creating all the main entries e.g. no dupes or no de-duping enabled
        if allOneTitle or (consolidateDuplicates and thisArticle.title in listOfUniques) or not consolidateDuplicates:

          if not thisArticle.nzbID in nzbItems:

            if thisArticle.moreInfo != "":
              log(7, funcName, 'Getting movie metadata:', thisArticle.moreInfo)
              metadata = movie_metadata.movie_metadata(thisArticle.moreInfo)
              oldTitle = thisArticle.title
              if metadata.metadata['title']: 
                thisArticle.title = metadata.title
              thisArticle.description = metadata.desc
              if thisArticle.title != oldTitle:
                thisArticle.description = "Original Title: " + oldTitle + "\n" + thisArticle.description
              thisArticle.duration = metadata.duration
              thisArticle.fanart = metadata.fanart
              thisArticle.thumb = metadata.thumb
              thisArticle.metadata = metadata.metadata
            nzbItems[thisArticle.nzbID] = thisArticle
            saveDict = True
          else:
            log(4, funcName + "Pulling item from cache")
            thisArticle = nzbItems[thisArticle.nzbID]
            #Log("Pulled article from cache.")

          try:
            subtitle = thisArticle.metadata['date'].strftime('%x')
          except:
            subtitle = ''
          dir.Append(DirectoryItem(Route(Article, theArticleID=thisArticle.nzbID), title=thisArticle.title, subtitle=subtitle, summary=thisArticle.attributes_and_summary, duration=thisArticle.duration, thumb=thisArticle.thumb, infoLabel=thisArticle.size, contextMenu=media_context_menu(itemID=thisArticle.nzbID, existingMenu=cm), air_release_date=get_metadata_date(thisArticle), contextKey=thisArticle.nzbID, contextArgs={}))
    
    #if saveDict:
      #Dict[nzbItemsDict] = nzbItems
      #pass
  if sort_by == 'NAME': dir.Sort('title')
  if sort_by == 'DATE': dir.Sort('air_release_date', descending=True)
  if (len(dir)+dupesFound)>=app.nzb.RESULTS_PER_PAGE:
    #Maybe we have more results, since newzbin only returns 100 at a time
    log(4, funcName + "len(dir): " + str(len(dir)) + ", adding an option to go to the next page")
    resultsSoFar = page * app.nzb.RESULTS_PER_PAGE
    page = page + 1
    dir.Append(Function(DirectoryItem(SearchMovies, "More than " + str(resultsSoFar) + " matches, Next Page"), value=value, title2=title2, maxResults=str(app.nzb.RESULTS_PER_PAGE), days=str(days), offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page))

  if offerExpanded:
    dir.Append(Function(DirectoryItem(SearchMovies, "[Expand this search...]"), value=value, title2="[expanded] " + title2, maxResults=str(int(maxResults)*ExpandedSearchMaxResultsFactor), days=str(int(days)*ExpandedSearchTimeFactor), offerExpanded=True, expandedSearch=True))
  #dir.Sort("title2")
  return dir

####################################################################################################
# General use functions
####################################################################################################
import subtitles
@route(routeBase + "SearchSubtitles/itemID={itemID}/file={file}/size={size}")
def SearchSubtitles(sender=None, key=None, itemID=None, file=None, size=0):
  funcName = "SearchSubtitles"
  log(7, funcName, 'itemID:', itemID, 'file:', file, 'size:', size)
  item = app.queue.getItem(itemID)
  if itemID == None or not item:
    return ObjectContainer(header='No item', message='No item selected, cannot search for subtitles.')
  if (file == None) or (size == 0):
    if not file: file = item.fullPathToMediaFile
    if not size: size = item.files[item.mediaFileName]
    if not file or not size:
      return ObjectContainer(header='Error', message='Error getting the media file or its size')
  subs = subtitles.Subtitles(file_path=file, filesize=size)
  all_subs = subs.SearchByOSHashAndFileSize()
  if len(all_subs) < 1:
    return ObjectContainer(header="No subtitles found", message="No subtitles are available for this item (yet?).")
  else:
    downloadedSubs = subs.DownloadSub(save_location=item.completed_path)
    return ObjectContainer(header="Subtitles Downloaded", message="Downloaded "+ str(len(downloadedSubs)) + " subtitles")

def checkForDupes(allEntries):
  funcName = "[checkForDupes]"

  dupesFound = 0
  listOfUniques = []
  listOfDupes = []

  # Outer loop to examine each entry
  for thisEntry in allEntries:
    thisDupeFound = False
    thisEntryTitle = thisEntry.title
    thisEntryID = thisEntry.nzbID
    log(5, funcName, 'Looking for dupes of "', thisEntryTitle, '"')

    # Inner loop that looks for duplicates for each entry
    if thisEntryTitle not in listOfDupes:
      log(6,funcName,"listOfDupes.count("+thisEntryTitle+"):", listOfDupes.count(thisEntryTitle))
      for eachEntry in allEntries:
        eachEntryTitle = eachEntry.title
        eachEntryID = eachEntry.nzbID
        if thisEntryID <> eachEntryID:
          log(6, funcName, 'Checking "',thisEntryTitle,'" against "',eachEntryTitle,'" for a duplicate')
          if str(thisEntryTitle) == str(eachEntryTitle) and thisEntryID <> eachEntryID:
            log(6,funcName,'Duplicate found of "',thisEntryTitle,'"')
            thisDupeFound = True
            #dupesFound = True
            listOfDupes.append(thisEntryTitle)
            log(6, funcName, 'Current list of Dupes:', listOfDupes)
            break
    else:
      log(5, funcName, "Pre-existing duplicate found: ", thisEntryTitle)
      thisDupeFound = True
      dupesFound += 1

    if not thisDupeFound:
      log(5, funcName, 'Unique Entry: "', thisEntryTitle,'"')
      listOfUniques.append(thisEntryTitle)
      log(6, funcName, 'Current list of Uniques:', listOfUniques)

  return dupesFound, listOfUniques, listOfDupes

####################################################################################################
def countEntries(title, allEntries):
  #Count up the number of times a title appears, not counting the current appearance
  funcName = "[countEntries]"
  countOfTitle = 0
  for eachentry in allEntries:
    thisEntryTitle = eachentry.title
    #thisEntryID = eachentry.xpath("report:id",namespaces=NEWZBIN_NAMESPACE)[0].text
    if title == thisEntryTitle:# and newzbinID <> thisEntryID:
      countOfTitle += 1

  log(4, funcName, 'Count of', title, ":", countOfTitle)
  return countOfTitle

# ####################################################################################################
# #Get all the nzbIDs associated with all the entries of the requested title
# def getAllEntriesIDs(title, allEntries):
#   funcName = "[getAllEntriesIDs]"
#   titleEntries = []
#   for eachentry in allEntries:
#     thisEntryTitle = eachentry.xpath("title")[0].text
#     thisEntryID = eachentry.xpath("report:id", namespaces=NEWZBIN_NAMESPACE)[0].text
#     if title == thisEntryTitle:
#       titleEntries.append(thisEntryID)
# 
#   log(4, funcName, "all IDs:", titleEntries)
#   return titleEntries
