from array import *
from common import *
from nntpclient import nntpClient
from queue import Queue
from configuration import *
from time import sleep
import sys

############################################################################################################
# Recently Done
# * Updated to Framework 2 (v1.2)
# + Fixed Newzbin for Newzbin2 compatibility
# + Integrated James Clarke's download code.  SABnzbd is no longer needed.
# + Fixed TV metadata
# + Fixed Movie Metadata
#
#
# Pre-Plex/Nine (Framework 2):
# + Added search by video quality, set in preferences
# + Added the ability to page through the return result set from newzbin (ie. page through >100 results)
# + Added log() function with a loglevel input to clean up the logs, and choose what gets logged and when
# + Added support for nzb matrix
# + Added support for newzbin2
#
############################################################################################################

#### TO DO
# 1. Allow for saving the queues over restarts
#	 Much of this code kind of exists, but does not consistenly work (see NWQueue implementation)'
#2. Allow the user to reprioritize download order

PREFIX      = "/video/newzworthy"

nzbServiceInfo = NZBService()
app = NewzworthyApp()
nzb = None
nntp = None
loggedInNZBService = False
loggedInNNTP = False

####################################################################################################
def Start():
  funcName = "[Start]"
  Plugin.AddPrefixHandler(PREFIX, MainMenu, 'Newzworthy', 'icon-default.png', 'art-default.png')
  DirectoryItem.thumb = R('icon-default.png')
  MediaContainer.art = R('art-default.png')
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("Lists", viewMode="List", mediaType="items")
  MediaContainer.title1 = 'Newzworthy'
  MediaContainer.content = 'Items'
  Resource.AddMimeType('video/x-matroska', '.mkv')
  Resource.AddMimeType('video/x-m4v', '.mp4')
  Resource.AddMimeType('video/x-m4v', '.mp4')
  Resource.AddMimeType('video/x-wmv', '.wmv')
  Resource.AddMimeType('video/x-msvideo', '.avi')

  HTTP.CacheTime=CACHE_INTERVAL
  HTTP.SetCacheTime=CACHE_INTERVAL
  HTTP.ClearCache()
  
  #Hack
  if nzbItemsDict in Dict:
    log(5, funcName, nzbItemsDict, 'found!')
    pass
  else:
    log(5, funcName, nzbItemsDict, 'not found, creating...')
    Dict[nzbItemsDict] = {}

  global loggedInNZBService
  global nzb
  NZBServiceSet = setNZBService()
  if NZBServiceSet:
    loggedInNZBService = nzb.performLogin(nzbServiceInfo)

  global nntp
  global loggedInNNTP
  
  nntp=nntpClient(app)

  log(8, funcName, 'NNTP Username, password, host, port, ssl:', nntp.nntpUsername, nntp.nntpPassword, nntp.nntpHost, nntp.nntpPort, nntp.nntpSSL)
  try:
    loggedInNNTP = nntp.connect()
  except:
    loggedInNNTP = False
  finally:
    nntp.disconnect()
    
  log(5, funcName, 'Newzworthy started')
  return True

####################################################################################################
import newzbin as nzbNewzbin
import nzbmatrix as nzbNzbmatrix
def setNZBService(retType='bool'): #valid return types: bool and object
  funcName='[setNZBService]'
  global nzb
  global loggedInNZBService
  global nzbServiceInfo

  loggedInNZBService = False
  serviceImported = False
  nzb = None
  serviceName=Prefs['NZBService']
  log(4,funcName,'importing NZBService:', serviceName)

  if serviceName=='Newzbin':
    log(4, funcName, 'importing newzbin')
    #import newzbin as nzb
    nzb = nzbNewzbin
    serviceImported=True
    nzbServiceInfo.newzbinUsername = getConfigValue(theDict=nzbConfigDict, key='newzbinUsername')
    log(6, funcName, 'newzbin Username:', nzbServiceInfo.newzbinUsername)
    nzbServiceInfo.newzbinPassword = getConfigValue(theDict=nzbConfigDict, key='newzbinPassword')
    log(8, funcName, 'newzbin Password:', nzbServiceInfo.newzbinPassword)
  elif serviceName=='NZBMatrix':
    log(4, funcName, 'importing nzbmatrix')
    #import nzbmatrix as nzb
    nzb = nzbNzbmatrix
    serviceImported=True
    log(6, funcName, 'Getting nzbMatrix Username')
    nzbServiceInfo.nzbmatrixUsername = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixUsername')
    log(6, funcName, 'nzbMatrix Username:', nzbServiceInfo.nzbmatrixUsername)
    nzbServiceInfo.nzbmatrixPassword = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixPassword')
    log(8, funcName, 'nzbMatrix Password:', nzbServiceInfo.nzbmatrixPassword)
    ##nzbServiceInfo.nzbmatrixAPIKey = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixAPIKey')
  log(4, funcName, serviceName, 'imported.')
  if retType == 'bool': return serviceImported
  if retType == 'object': return nzb

####################################################################################################
def ValidatePrefs():
  funcName = "[ValidatePrefs] "
  log(2, funcName + "Restarting Newzworthy Plugin")
  global app
  try:
    app.nntpManager.disconnect_all()
  except:
    pass
  Core.runtime.restart()

####################################################################################################
@route(routeBase + 'restart')
def RestartNW():
  global app
  try:
    app.nntpManager.disconnect_all()
  except:
    pass
  Core.runtime.restart()
  
####################################################################################################
@route(routeBase + 'MainMenu')
def MainMenu():
  funcName = '[MainMenu]'
  global loggedInNZBService
  global nzbServiceInfo
  global loggedInNNTP
  global nntp
  global app
  global nzb
  
  # Set the right NZB servers to use
  if not loggedInNZBService:
    log(3, funcName, 'Not logged into NZB Service, doing it now')
    # try to log into the NZB Service...
    nzb = setNZBService(retType='object')
    loggedInNZBService = nzb.performLogin(nzbServiceInfo, forceRetry=True)
    log(3, funcName + "nzb login:", str(loggedInNZBService))
  else:
    log(3, funcName, "Already logged into nzb")
    
  if not loggedInNNTP:
    log(3, funcName, 'Not logged into NNTP, doing it now')
    # try to log into the nntp service
    nntp = nntpClient(app)
    try:
      loggedInNNTP = nntp.connect()
    except:
      loggedInNNTP = False
    finally:
      nntp.disconnect()
    log(3, funcName, "nntp login:", loggedInNNTP)
  else:
    log(3, funcName, "Already logged into nntp")

  # Empty context menu, since there aren't any useful contextual options right now.
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
  dir = MediaContainer(contextMenu=cm, noCache=True, viewGroup="Lists")
  
  if app.updater.updateNeeded:
    dir.Append(DirectoryItem(Route(Update), title=L('NW_UPDATE_AVAIL'), summary=app.updater.stableUpdateURL, thumb=R('update.png')))
  # Sub-menu for TV
  if loggedInNZBService and loggedInNNTP:
    log(5, funcName, 'Logged in, showing TV & Movie menu options')
    dir.Append(Function(DirectoryItem(BrowseTV, title=("Go to TV"), thumb=R('tv.jpg'), contextKey="a", contextArgs={})))
    # Sub-menu for Movies
    dir.Append(Function(DirectoryItem(BrowseMovies, title=("Go to Movies"), thumb=R('movies.jpg'),contextKey="a", contextArgs={})))
    # Special case just for searching by newzbinID
    #if(bool(Prefs['ShowSearchByNewzbinID']) and Prefs['NZBService']=="Newzbin"):
    #  dir.Append(Function(InputDirectoryItem(Search, title=("Search by Newzbin ID"), prompt=("Search by Newzbin ID"), thumb=R('search.png'), contextKey="a", contextArgs={}), category="99"))
  else:
    log(5, funcName, 'Not logged in, showing option to update preferences')
    if not loggedInNZBService:
      dir.Append(Function(DirectoryItem(configure, title=("Not logged in to " + Prefs["NZBService"]), thumb=R("x_red.png"), contextKey="a", contextArgs={})))
    if not loggedInNNTP:
      dir.Append(Function(DirectoryItem(configure, title=("Not logged in to Usenet (NNTP)"), thumb=R("x_red.png"), contextKey="a", contextArgs={})))

  # Show the troubleshooting options.  Not recommended, but can be very useful.
  if bool(Prefs['ShowDiags']):
    dir.Append(DirectoryItem(Route(diagsMenu), title="Troubleshooting/Diagnostics", thumb=R('troubleshooting.png')))
  else:
    log(7, funcName, 'NOT showing (ie. hiding) diagnostic menu options')

  # Show the preferences option
  log(7, funcName, 'Showing Preferences')
  dir.Append(PrefsItem(L("Preferences"), thumb=R('preferences.png'), contextKey="a", contextArgs={}))
  log(7, funcName, 'Showing setup options')
  dir.Append(Function(DirectoryItem(configure, title="Setup servers, usernames, and passwords", thumb=R('configuration.png'), contextKey="a", contextArgs={})))
  log(7, funcName, 'Showing Manage Queue')
  dir.Append(DirectoryItem(Route(manageQueue), title=("Manage Download Queue (" + str(len(app.queue.downloadableItems)) + ")"), thumb=R('download_queue.png')))
  log(7, funcName, 'Showing Completed Queue Management option')
  dir.Append(DirectoryItem(Route(manageCompleteQueue), title=("View Completed Downloads (" + str(len(app.queue.completedItems)) + ")"), thumb=R('check_green.png')))
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
  dir.Append(Function(DirectoryItem(clearArticleDict, title="Clear the cache", thumb=R('trashcan.png'), contextKey="a", contextArgs={})))
  log(7, funcName, 'Showing "Delete all Downloaded Files"')
  dir.Append(Function(DirectoryItem(deleteAllDownloads, title="Delete all downloaded files", thumb=R('trashcan.png'), contextKey="a", contextArgs={})))
  dir.Append(DirectoryItem(Route(clearAllQueues), title="Clear all the queues", thumb=R('trashcan.png')))
  log(7, funcName, 'Showing "Show All Dicts"')
  dir.Append(Function(DirectoryItem(showAllDicts, title="Show All Dicts", contextKey="a", thumb=R('search.png'), contextArgs={})))
  #log(7, funcName, 'Show restart plugin')
  dir.Append(DirectoryItem(Route(RestartNW), title='Restart Newzworthy Plugin', contextKey="a", contextArgs={}))
  return dir

####################################################################################################
@route(routeBase + "Update")
def Update():
  funcName = '[Update]'
  global app
  if app.updater.updateNeeded:
    #app.updater.updateToStable()
    message = "Update available, download at: " + app.updater.stableUpdateURL
  else:
    message = "No Updates Available"
  return MessageContainer("Updater", message)
####################################################################################################
def clearArticleDict(sender):
  funcName = "[clearArticleDict]"
  log(1, funcName, 'articleDict before clearing:', Dict[nzbItemsDict])
  Dict[nzbItemsDict] = {}
  log(1, funcName, 'articleDict after clearing:', Dict[nzbItemsDict])
  return MessageContainer("Cache Cleared", "All cached items have been cleared.")

@route(routeBase + 'clearAllQueues')
def clearAllQueues():
  funcName = "[clearAllQueues]"
  app.queue.resetItemQueue()
  app.downloader.resetArticleQueue()
  return MessageContainer("Queues Cleared", "All queues have been cleared.")
  
def deleteAllDownloads(sender):
  funcName = "[deleteAllDownloads]"
  media_path = Core.storage.join_path(Core.storage.data_path, 'Media')
  for dir_obj in Core.storage.list_dir(media_path):
    try:
      Core.storage.remove_tree(Core.storage.join_path(media_path, dir_obj))
    except:
      log(3, funcName, 'Could not delete', dir_obj)
  return MessageContainer("Files Deleted", "All downloaded files have been deleted.")
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
        keyTitle = thisDict + ":" + key + ": " + str(theDict[key])
        dir.Append(Function(DirectoryItem(StupidUselessFunction, title=keyTitle), key=keyTitle))
    except:
      log(5, funcName, str(thisDict), 'not a dict type, assuming it''s a list or other iterable object')
      for item in Dict[thisDict]:
        keyTitle = thisDict + ": " + str(item)
        dir.Append(Function(DirectoryItem(StupidUselessFunction, title=keyTitle), key=keyTitle))
  return dir

####################################################################################################
def BrowseMovies(sender='nothing'):
  # Empty context menu, since there aren't any useful contextual options right now.
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
  dir = MediaContainer(contextMenu=cm, noCache=True, title2="Movies")

  if nzb.supportsGenres():
    dir.Append(Function(DirectoryItem(BrowseMovieGenres, title=("Browse Recent Movies by Genre"), contextKey="a", contextArgs={}), filterBy="Video Genre"))
  else:
    dir.Append(Function(DirectoryItem(SearchMovies, title=("Browse Recent Movies"), contextKey="a", contextArgs={}), value="", title2="All Recent Movies", days=MovieSearchDays_Default, maxResults=str(nzb.RESULTS_PER_PAGE)))

  dir.Append(Function(InputDirectoryItem(Search, title=("Search Movies"), prompt=("Search Movies"), thumb=R('search.png'), contextKey="a", contextArgs={}), category="6"))
  return dir
####################################################################################################
def BrowseTV(sender='nothing'):

  # Empty context menu, since there aren't any useful contextual options right now.
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="No Options")))
  dir = MediaContainer(viewGroup='Lists', contextMenu=cm, noCache=True, title2="TV")
  

  if nzb.supportsGenres(): dir.Append(Function(DirectoryItem(BrowseTVGenres,         title=("Browse Recent TV by Genre"), contextKey="a", contextArgs={}), filterBy="Video Genre"))
  dir.Append(Function(InputDirectoryItem(Search,     title=("Search TV"), prompt=("Search TV"), thumb=R('search.png'), contextKey="a", contextArgs={}), category="8"))
  try:
    if len(Dict[TVFavesDict])>=1:
      dir.Append(Function(DirectoryItem(BrowseTVFavorites,	title=("Browse TV Favorites (1 Day)"), thumb=R('one_day.png'), contextKey="a", contextArgs={}), days="1"))
      dir.Append(Function(DirectoryItem(BrowseTVFavorites,	title=("Browse TV Favorites (1 Week)"), thumb=R('one_week.png'), contextKey="a", contextArgs={}), days="7"))
      dir.Append(Function(DirectoryItem(BrowseTVFavorites,	title=("Browse TV Favorites (1 Month)"), thumb=R('one_month.png'), contextKey="a", contextArgs={}), days="30"))
      dir.Append(Function(DirectoryItem(BrowseTVFavorites,	 title=("Browse TV Favorites (All)"), thumb=R('infinity.png'), contextKey="a", contextArgs={}), days="0"))

  except:
    pass
  #Always let the user manage their favorites
  dir.Append(Function(DirectoryItem(ManageTVFavorites,	 title=("Manage the list of TV Favorites"), contextKey="a", contextArgs={})))  
  return dir

####################################################################################################
def ManageTVFavorites(sender='nothing'):
  funcName = "[ManageTVFavorites] "
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
    dir.Append(Function(DirectoryItem(SearchTV, title=title, contextKey=title, contextArgs={}), value=nzb.concatSearchList([title]), title2=title, days=TVSearchDays_Default, maxResults=str(nzb.RESULTS_PER_PAGE)))

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
def BrowseTVFavorites(sender, days=TVSearchDays_Default):
  funcName = "[BrowseTVFavorites] "
  faves=Dict[TVFavesDict]
  
  if len(faves)>=1:
    try:
      log(4, funcName, 'Retrieved these favorites:',faves)
      query = nzb.concatSearchList(faves)

      log(3, funcName + "query: " + query)
      dir = SearchTV(sender, value=query, title2="Favorites", days=days)
      return dir
    except:
      return MessageContainer("No favorites", "You have not saved any favorite TV shows to search.  Add some favorites and then try again.")
  else:
    return MessageContainer("No favorites", "You have not saved any favorite TV shows to search.  Add some favorites and then try again.")

####################################################################################################
def SearchTV(sender, value, title2, days=TVSearchDays_Default, maxResults=str(0), offerExpanded=False, expandedSearch=False, page=1, invertVideoQuality=False, allOneTitle=False):
  funcName = "[SearchTV] "
  global nzb
  # Determine if we will be consolidating duplicates to a single entry
  if allOneTitle:
    consolidateDuplicates = False
  else:
    consolidateDuplicates = Prefs['consolidateTVDuplicates']

  queryString = value

  # I'm searching TV, I know the category
  category = nzb.CAT_TV

  nzbItems = Dict[nzbItemsDict]
  allTitles = []

  # Add any video format filters
  VideoFilters = nzb.getTVVideoFilters()
  log(3, funcName + "Retrieved Video Filters: " + VideoFilters)
  log(4, funcName + "About to add Video Filters, current queryString: " + queryString)
  if len(VideoFilters)>=1:
    #This didn't work the way I wanted
    #if invertVideoQuality:
    #  log(4, funcName + "Inverting Video Filters")
    #  queryString += " -(" + VideoFilters + ")"
    #else:
    #This would be the else statement... re-indent if you figure out the video filtering
    queryString += " " + VideoFilters
  log(4, funcName + "Added Video Filters, current queryString: " + queryString)
  # Add any language filters
  Languages = nzb.getTVLanguages()
  if len(Languages)>=1:
    queryString += " " + Languages
  #Make the queryString usable by the intertubes
  queryString = encodeText(queryString)
  log(4, funcName + "Encoded queryString: " + queryString)

  # Calculate the right number of seconds
  period = nzb.calcPeriod(days)

  #make a meaningful title for the window
  thisTitle = "TV > "
  if page>1: thisTitle += "Page " + str(page) + " > "
  thisTitle += title2

  dir = MediaContainer(viewGroup='Details', title2=thisTitle, noCache=False)

  # Go get the data
  try:
    allEntries = nzb.search(category, queryString, period, page)
  except:
    return MessageContainer('Error searching', "There was an error trying to search.  Please try again later or check your username, password, and membership status.")
  if not len(allEntries)>=1:
    return MessageContainer(header="No Matching Results", message="Your search did not yield any matches")

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
  def doTVMetaDataLookups():

    for entry in allEntries:
      @task
      def IterableElement1(thisArticle = entry):

        # Check to see if this is a duplicate and we should be de-duping
        # First pass will handle creating all the main entries e.g. no dupes or no de-duping enabled
        if allOneTitle or (consolidateDuplicates and thisArticle.title in listOfUniques) or not consolidateDuplicates:

          if not thisArticle.nzbID in nzbItems:

            thisArticle.mediaType = 'TV'
            thisArticle.subtitle = ""

            #log(5, funcName, "checking len(moreInfoURL):", len(thisArticle.moreInfoURL))
            if len(thisArticle.moreInfoURL)>1:
              log(5, funcName, "think we have a meaningful URL:'" + thisArticle.moreInfoURL + "' Count of 'episodes':", thisArticle.moreInfoURL.count("episodes"))
              if thisArticle.moreInfoURL.count("episodes") > 0  or thisArticle.moreInfoURL.count("search.php?search=") > 0: #don't mess with whole season dvd rips
                log(4, funcName, 'found more than 0 episodes in the url:', thisArticle.moreInfoURL)
                tvRageDict = getTVRage_metadata(thisArticle.moreInfoURL)
                if tvRageDict:
                  if tvRageDict["title"] != "" : thisArticle.title = tvRageDict["title"]
                  thisArticle.description = "Size: " + thisArticle.size + "\n\n" + tvRageDict["summary"]
                  thisArticle.subtitle = "S" + tvRageDict["season"] + "E" + tvRageDict["episode"] + " (" + tvRageDict["airDate"] + ")"
                  thisArticle.rating = tvRageDict["votes"]
                  thisArticle.thumb = tvRageDict["thumb"]
                  thisArticle.duration = tvRageDict["duration"]
              else:
                log(4, funcName, 'Did not find keyword "episodes" or "search.php" in', thisArticle.moreInfoURL, 'for:', thisArticle.title)
            else:
              log(5, funcName, 'No TVRageURL found for:', thisArticle.title)


            log(4, funcName, "Adding \"" + thisArticle.title + "\" to the dir")
            dir.Append(DirectoryItem(Route(Article, theArticleID=thisArticle.nzbID), title=thisArticle.title, subtitle=thisArticle.subtitle, summary=thisArticle.attributes_and_summary, duration=thisArticle.duration, thumb=thisArticle.thumb, rating=thisArticle.rating, infoLabel=thisArticle.size))
#             articleItem = Function(DirectoryItem(Article, thisArticle.title, thisArticle.subtitle, summary=thisArticle.summary, duration=thisArticle.duration, thumb=thisArticle.thumb, rating=thisArticle.rating, infoLabel=thisArticle.size), theArticleID=thisArticle.nzbID) #title2=title, fanart=fanart, thumb=thumb, rating=rating, duration=duration)

            # Add the item to the persistent-ish cache
            nzbItems[thisArticle.nzbID] = thisArticle
            saveDict = True
            #dir.Append(articleItem)

          else: # The nzbID is already in the dict, therefore we can just pull it from cache
            log(4, funcName, "Cached: Adding \"" + nzbItems[thisArticle.nzbID].title + "\" from the cache.")
            thisArticle = nzbItems[thisArticle.nzbID]
            dir.Append(DirectoryItem(Route(Article, theArticleID=thisArticle.nzbID), title=thisArticle.title, subtitle=thisArticle.subtitle, summary=thisArticle.attributes_and_summary, duration=thisArticle.duration, thumb=thisArticle.thumb, rating=thisArticle.rating, infoLabel=thisArticle.size))
#            dir.Append(Function(DirectoryItem(Article, thisArticle.title, thisArticle.subtitle, summary=thisArticle.summary, duration=thisArticle.duration, thumb=thisArticle.thumb, rating=thisArticle.rating, infoLabel=thisArticle.size), theArticleID=thisArticle.nzbID))

        # Now handle the case where we want to consolidate dupes and we have more than one entry.
        # Note that we are still only returning some number of results in a single query to newzbin
        # and we could end up with duplicates across pages... that case is not handled (yet?)
        elif (consolidateDuplicates) and (thisArticle.title in listOfDupes) and (not allOneTitle):
          countOfEntries = countEntries(thisArticle.title, allEntries)
          log(4, funcName, thisArticle.title, "is a duplicate with", countOfEntries, "occurrences.")

          # OK, we'll build a new query with all the dupes
          numEntries = str(countOfEntries) + " Entries"
          dir.Append(Function(DirectoryItem(SearchTV, title=thisArticle.title, infoLabel=numEntries), sender=sender, value=thisArticle.title, title2=thisArticle.title, days=days, maxResults=maxResults, allOneTitle=True))
          listOfDupes.remove(thisArticle.title)
          #lenOfDir+=1

  if saveDict:
    log(4, funcName, 'Saving Dict:', nzbItemsDict)
    Dict[nzbItemsDict] = nzbItems
    #pass
  #dir.nocache=1

  # We only get back so many results in our request.  If we hit that limit, let's assume there's more behind these
  # results and offer the user the option to go to the next page of results.
  if (len(allEntries))>=nzb.RESULTS_PER_PAGE:
    log(4, funcName + "len(allEntries): " + str(len(allEntries)) + ", adding an option to go to the next page")
    resultsSoFar = page * nzb.RESULTS_PER_PAGE
    page+=1
    log(4, funcName, 'Page being sent to next page:', page)
    dir.Append(Function(DirectoryItem(SearchTV, "More than " + str(resultsSoFar) + " matches, Next Page"), value=value, title2=title2, maxResults=str(nzb.RESULTS_PER_PAGE), days=str(days), offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page, invertVideoQuality=invertVideoQuality))
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
    nzbItems = Dict[nzbItemsDict]
    theArticle=nzbItems[theArticleID]
  
  #Determine what you want to show as the secondary window title
  if theArticle.mediaType=='TV':
    log(7, funcName, theArticle.title, "is a TV show")
    title2 = "TV > " + theArticle.title
  elif theArticle.mediaType=='Movie':
    log(7, funcName, theArticle.title, "is a Movie")
    title2 = "Movies > " + theArticle.title
  else:
    log(3, funcName, theArticle.title, "is an unknown media type (i.e. not a TV show nor a movie")
    title2 = theArticle.title

  dir = MediaContainer(viewGroup='Details', title2=title2, noCache=True, noHistory=False, autoRefresh=1)
  try:
    if theArticle.fanart != "":
      dir.art = theArticle.fanart
  except:
    pass

  #art = Function(DirectoryItem(StupidUselessFunction, subtitle=theArticle.subtitle))
  if app.queue.getItem(theArticle.nzbID) == False:
    #dir.Append(Function(DirectoryItem(StupidUselessFunction, title=theArticle.title, summary=theArticle.summary, thumb=theArticle.thumb, subtitle=theArticle.subtitle), key="a"))
    dir.Append(DirectoryItem(Route(AddReportToQueue, nzbID=theArticle.nzbID), title=L('ITM_QUEUE'), thumb=theArticle.thumb, subtitle=theArticle.title, summary=theArticle.attributes_and_summary))

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
    item = app.queue.getItem(theArticle.nzbID)
    dir.Append(Function(DirectoryItem(StupidUselessFunction, title=theArticle.title, summary=theArticle.summary, thumb=theArticle.thumb, subtitle=theArticle.subtitle), key="a"))

    if item.downloading:
      #If it's ready to play, give the user the option here
      progress = 'Progress: ' + (('%.1f' % item.percent_complete) + '%')
      speed = 'Speed: ' + str(convert_bytes(app.nntpManager.speed))
      rtp = 'Ready to play: ' + (('%.1f' % item.play_ready_percent) + '%')
      progress_speed = progress + '\n' + speed
      rtp_progress_speed = rtp + '\n' + progress_speed
      if item.play_ready:
        dir.Append(VideoItem(Route(StartStreamAction, id=item.id), title=L('DL_PLAY_DL'), subtitle=theArticle.subtitle, thumb=R('play_yellow.png'), infoLabel=(('%.1f' % item.percent_complete)+'%'), summary=(progress_speed + '\n' + theArticle.summary)))
      else:
        dir.Append(DirectoryItem(Route(StupidUselessFunction, key="a"), title=L('DL_DOWNLOADING_PLAY') + ReadyToPlayText(item.play_ready_time), thumb=R('download_green.png'), subtitle="Downloading enough to start playing", infoLabel=(('%.1f' % item.play_ready_percent)+'%'), summary=rtp_progress_speed))
      dir.Append(DirectoryItem(Route(CancelDownloadAction, id=item.id), title=L('CANCEL_DL'), thumb=R('trashcan.png'), subtitle='Cancel and delete progress'))
    elif item.complete:
      #Show the option to remove the file
      dir.Append(VideoItem(Route(StartStreamAction, id=item.id), title=L('PLAY_DL'), thumb=R('play_green.png')))
      dir.Append(DirectoryItem(Route(RemoveItemAction, id=item.id), title=L('REMOVE_DL'), thumb=R('trashcan.png')))
    else: #Must be queued for downloading
      dir.Append(DirectoryItem(Route(StupidUselessFunction, key="a"), title=L('DL_QUEUED'), thumb=R('download_green.png'), subtitle="Download queued"))
      dir.Append(DirectoryItem(Route(CancelDownloadAction, id=item.id), title=L('CANCEL_DL'), thumb=R('trashcan.png')))
    #Show the option to delete the item

  if len(app.queue.downloadableItems) >= 1:
    dir.Append(DirectoryItem(Route(manageQueue), title=("View Download Queue (" + str(len(app.queue.downloadableItems)) + " items)"), thumb=R('download_queue.png')))
  if len(app.queue.completedItems) >= 1:
    dir.Append(DirectoryItem(Route(manageCompleteQueue), title=("View Completed Queue (" + str(len(app.queue.completedItems)) + " items)"), thumb=R('check_green.png')))

  #dir.Append(addToQueue)
  return dir

####################################################################################################
@route(routeBase + 'AddReportToQueue/{nzbID}')
def AddReportToQueue(nzbID, article='nothing'):
  funcName = "[AddReportToQueue]"
  #global app
  log(5, funcName, 'Setting queue object, should be using previously initialized app object''s queue')
  queue = app.queue
  log(5, funcName, 'queue object set')
  if article=='nothing':
    nzbItems = Dict[nzbItemsDict]
    article = nzbItems[nzbID]
  item = queue.add(nzbID, nzb, article)
  #item.download()
  log(5, funcName, 'Items queued:', len(app.queue.items))
  header = 'Item queued'
  message = '"%s" has been added to your queue' % item.report.title
  return MessageContainer(header, message)

####################################################################################################
@route(routeBase + 'manageCompleteQueue')
def manageCompleteQueue():
  funcName = "[manageCompleteQueue]"

  # Some cleanup to avoid errors
  #if app.stream_initiator != None: app.stream_initiator = None


  dir = MediaContainer(viewGroup="Details", noCache=True, autoRefresh=10)
  
  if len(app.queue.completedItems) > 0:
    for item in app.queue.completedItems:
      dir.Append(DirectoryItem(Route(Article, theArticleID=item.id), title=item.report.title, subtitle=item.report.subtitle, summary=item.report.attributes_and_summary))
  else:
    dir.Append(DirectoryItem(Route(StupidUselessFunction, key=''), title="No Completed Downloads", subtitle="There are no completed items to display", summary=""))   
  return dir
####################################################################################################
@route(routeBase + 'manageQueue')
def manageQueue():
  funcName = "[manageQueue]"

  # First check if there's anything in the queue
  log(6, funcName, 'Items in download queue:', len(app.queue.downloadableItems))
#  if len(app.queue.downloadableItems) == 0:
#    return MessageContainer('Nothing in queue', 'There are no items in the queue')
    #MainMenu()
  
  # Some cleanup to avoid errors
  #log(6, funcName, 'Clearing app.stream_initiator:', (app.stream_initiator != None))
  #if app.stream_initiator != None: app.stream_initiator = None
  
  # Display the contents of the queue
  log(7, funcName, 'Creating dir')
  dir = MediaContainer(viewGroup="Details", noCache=True, autoRefresh=1)
  #if app.downloader.notPaused:
  #  dir.Append(DirectoryItem(Route(pauseDownload), title="Pause Downloading", subtitle="Temporarily suspend all downloads", summary=""))
  #else:
  #  dir.Append(DirectoryItem(Route(resumeDownload), title="Resume Downloading", subtitle="You temporarily suspended downloads.  Resume them now.", summary=""))
  
  if len(app.queue.downloadableItems) == 0:
    dir.Append(DirectoryItem(Route(StupidUselessFunction, key=""), title="0 items in download queue", subtitle="Nothing to download", summary=""))
  log(7, funcName, 'Looking at each item in queue')
  for item in app.queue.downloadableItems:
    log(7, funcName, 'Examining:', item.report.title)
    subtitle = ' '
    summary = ' '
    progress = 'Progress: ' + (('%.1f' % item.percent_complete) + '%')
    speed = 'Speed: ' + str(convert_bytes(app.nntpManager.speed))
    progress_speed = progress + '\n' + speed
    #if item.complete:
    #  log(7, funcName, 'item.complete:', item.complete)
    #  subtitle = L('DL_COMPLETE')
    #  summary = progress_speed + "\n" + item.report.summary

    if item.play_ready:
      log(7, funcName, 'item.play_ready:', item.play_ready)
      subtitle = L('DL_PLAY_READY')      
      summary = progress_speed

    elif item.downloading:
      log(7, funcName, 'item.downloading:', item.downloading)
      log(7, funcName, 'item.play_ready_time:', item.play_ready_time)
      # All these strings can be found in the Strings folder of the bundle
      
      tm = item.play_ready_time
      if tm == 0:
        subtitle = L('DL_PLAY_READY')
        summary = progress_speed
      else:
#         subtitle = L('DL_DOWNLOADING')
#         if tm < 3:
#           ttp = L('DL_SUM_PR_FEW_SECS')
#         elif tm > 60:
#           mins = tm / 60
#           secs = tm % 60
#           if mins == 1:
#             key = 'DL_SUM_PR_MIN_SECS'
#           else:
#             key = 'DL_SUM_PR_MINS_SECS'
#           ttp = F(key, mins, secs)
#         else:
#           ttp = F('DL_SUM_PR_SECS', tm)
        ttp = ReadyToPlayText(tm)
        summary += ttp + "\n" + progress_speed

    else:
      subtitle = L('DL_QUEUED')
      #summary = item.report.summary
    summary += "\n" + item.report.summary
    log(7, funcName, 'Queue item:', item.report.title+': subtitle:', subtitle, 'summary:', summary)
    log(7, funcName, 'Found in queue:', item)
    
    dir.Append(DirectoryItem(Route(Article, theArticleID=item.id), title=item.report.title, subtitle=subtitle, summary=summary))

  return dir

def ReadyToPlayText(tm):
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

  if not item: return MessageContainer("No Item", "Did not find item")
  if item.play_ready:
    #a = Redirect(item.stream)
    return Redirect(item.stream)

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
  item = app.queue.getItem(id)
  if item.downloading:
    log(5, funcName, "Pausing the downloader task")
    app.downloader.stop_download_thread()
    app.downloader.resetArticleQueue()
    #while app.downloader.active_clients > 0:
      #log(7, funcName, "waiting for the downloads to stop.")
      #sleep(1)
  # Remove the item from the queue
  app.queue.items.remove(item)
  folderDeleted = item.delete()
  log(7, funcName, 'deleted folder:', folderDeleted)
  # Restart the downloader task
  if item.downloading:
    log(5, funcName, "Restarting download client tasks")
    app.downloader.resetArticleQueue()
    app.downloader.notPaused = True
    app.downloader.start_download_thread()
  
  #return True


@route(routeBase + 'queue/{id}/remove')
def RemoveItemAction(id):
  funcName = "[RemoveItemAction]"
  log(5, funcName, "Removing id", id, "from the queue")
  item = app.queue.getItem(id)
  folderDeleted = item.delete()
  log(7, funcName, 'Folder deleted:', folderDeleted)
  if folderDeleted:
    app.queue.items.remove(item)
  else:
    return MessageContainer("Error", "Item not deleted: " + str(item))
  
  return MessageContainer("Successfully Deleted", "The item was successfully deleted.")
#  return True

####################################################################################################
def Search(sender, query, category):
  funcName = "[Search] "
  SearchList = []
  SearchList.append(query)
  usableQuery=nzb.concatSearchList(SearchList)

  if category == "6": #movies
    dir = SearchMovies(sender, value=usableQuery, title2=query, days=TVSearchDays_Default, maxResults=str(nzb.RESULTS_PER_PAGE), offerExpanded=False)

  elif category == "8": #tv
    dir = SearchTV(sender, value=usableQuery, title2=query, days=MovieSearchDays_Default, maxResults=str(nzb.RESULTS_PER_PAGE), offerExpanded=False)
    
  elif category == "99": #newzbinID search
    url = "http://www.newzbin.com/browse/post/" + query
    newzbinHtml = HTTP.Request(url)
    title = HTML.ElementFromString(newzbinHtml).xpath("//table[@class='dataIrregular']//tr//td")[0].text_content() #.encode('utf-8')
    title = title.splitlines()[-2].strip()
    if newzbinHtml.count("imdb.com") > 0: #must be a movie
      pass
    elif newzbinHtml.count("tvrage.com") > 0: #must be a tv show
      pass
    log(3, funcName + title)
    dir = Article(sender=sender, newzbinID=query, title2=title, subtitle=title) #, replaceParent=False)
  return dir

####################################################################################################
def BrowseMovieGenres(sender, filterBy):
  funcName = "[BrowseMovieGenres] "
  # Empty context menu, since there aren't any useful contextual options right now.
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="No Options")))
  dir = MediaContainer(contextMenu=cm, noCache=True, viewGroup='Details', title2='Movies by Genre')

  #next item is the "all genres" item.
  dir.Append(Function(DirectoryItem(SearchMovies, title="All Genres", contextKey="a", contextArgs={}), value='', title2='All Genres', days=MovieSearchDays_Default, maxResults=str(nzb.RESULTS_PER_PAGE)))
  filterHTML = HTTP.Request(nzb.SEARCH_URL)
  for genre in HTML.ElementFromString(filterHTML).xpath('//optgroup[@label="' + filterBy + '"]/option'):
    title = genre.text.strip() #.encode('utf-8')
    log(4, funcName + "title: " + str(title))
    attrTitle = "a:VideoG~" + title
    dir.Append(Function(DirectoryItem(SearchMovies, title=title, contextKey="a", contextArgs={}), value=attrTitle, title2=title, days=MovieSearchDays_Default, maxResults=str(nzb.RESULTS_PER_PAGE)))
  return dir

####################################################################################################
def BrowseTVGenres(sender, filterBy):
  funcName = "[BrowseTV] "

  # Empty context menu, since there aren't any useful contextual options right now.
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="No Options")))

  dir = MediaContainer(viewGroup='Details', title2='TV by Genre')
  # next item is the "all genres" item.
  dir.Append(Function(DirectoryItem(SearchTV, title="All Genres"), value="", title2='All Genres', days=TVSearchDays_Default, maxResults=str(nzb.RESULTS_PER_PAGE), offerExpanded=False))

  # Get the list of genres from the nzb service
  filterHTML = HTTP.Request(nzb.SEARCH_URL)

  # Present each genre in a list
  for genre in HTML.ElementFromString(filterHTML).xpath('//optgroup[@label="' + filterBy + '"]/option'):
    title = genre.text.strip()
    log(4, funcName + "title: " +str(title))
    # for newzbin, searching by attribute name
    attrTitle = "a:VideoG~" + title
    dir.Append(Function(DirectoryItem(SearchTV, title=title), value=attrTitle, title2=title, days=TVSearchDays_Default, maxResults=str(nzb.RESULTS_PER_PAGE), offerExpanded=False))
  return dir

####################################################################################################
def SearchMovies(sender, value, title2, maxResults=str(0), days=MovieSearchDays_Default, offerExpanded=False, expandedSearch=False, page=1, invertVideoQuality=False, allOneTitle=False):
  funcName = "[SearchMovies] "
  log(4, funcName + "Incoming variables: value=" + value + ", title2=" + title2 + ", maxResults=" + maxResults + ", days=" + days + ", page=" + str(page))

  # Determine if we will be consolidating duplicates to a single entry
  if allOneTitle:
    consolidateDuplicates = False
  else:
    consolidateDuplicates = bool(Prefs['consolidateMovieDuplicates'])

  queryString = value

  # I know we are looking for movies
  category = nzb.CAT_MOVIES


  # Add any video format filters
  VideoFilters = nzb.getMovieVideoFilters()
  log(3, funcName + "Retrived Video Filters: " + VideoFilters)
  log(4, funcName + "About to add Video Filters, current queryString: " + queryString)
  if len(VideoFilters)>=1: queryString += " " + VideoFilters
  log(4, funcName + "Added Video Filters, current queryString: " + queryString)
  # Add any language filters
  Languages = nzb.getMovieLanguages()
  if len(Languages)>=1: queryString += " " + Languages
  #Make the queryString usable by the intertubes
  queryString = encodeText(queryString)
  log(4, funcName + "Encoded queryString: " + queryString)

  # Calculate the right number of seconds
  period = nzb.calcPeriod(days)

  #make a meaningful title for the window
  thisTitle = "Movies > "
  if page>1: thisTitle += "Page " + str(page) + " > "
  thisTitle += title2

  nzbItems = Dict[nzbItemsDict]
  dir = MediaContainer(viewGroup='Details', title2=thisTitle, noCache=False)
  saveDict = True

  # Go get the data
  allEntries = nzb.search(category, queryString, period, page)
  if not len(allEntries)>=1:
    return MessageContainer(header="No Matching Results", message="Your search did not yield any matches")

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

            if thisArticle.moreInfo != "": # and Prefs.Get('searchMetadata'):
              log(7, funcName, 'Getting imdb metadata:', thisArticle.moreInfo)
              thisArticle.imdbDict = getIMDB_metadata(thisArticle.moreInfo)
              log(8, funcName, 'Got imdb data:', thisArticle.imdbDict)
              log(7, funcName, 'Getting tmdb metadata:', thisArticle.moreInfo)
              thisArticle.tmdbDict = tmdb_getMetaData(thisArticle.moreInfo)
              log(7, funcName, 'Getting mpdbThumb:', thisArticle.moreInfo)
              thisArticle.mpdbThumb = movieposterdb_getThumb(thisArticle.moreInfo)
              try:
                thisArticle.description = thisArticle.imdbDict["desc"]#.encode('utf-8')
                try:
                  if thisArticle.description == "":
                    thisArticle.description = tmdbDict["desc"]
                except:
                  pass
              except:
                pass
              try:
                thisArticle.thumb = thisArticle.imdbDict["thumb"]
                if thisArticle.thumb == "":
                  thisArticle.thumb = mpdbThumb
                  if thisArticle.thumb == "":
                    thisArticle.thumb = tmdbDict["thumb"]
              except:
                pass
              try:
                thisArticle.duration = str(int(thisArticle.imdbDict["duration"]))
              except:
                pass
              try:
                thisArticle.fanart = tmdbDict["fanart"]
              except:
                pass
              try:
                thisArticle.rating = thisArticle.imdbDict["rating"]
              except:
                thisArticle.rating = ""

            nzbItems[thisArticle.nzbID] = thisArticle
            saveDict = True
          else:
            log(4, funcName + "Pulling item from cache")
            thisArticle = nzbItems[thisArticle.nzbID]
            #Log("Pulled article from cache.")

          dir.Append(DirectoryItem(Route(Article, theArticleID=thisArticle.nzbID), title=thisArticle.title, subtitle=thisArticle.reportAge, summary=thisArticle.attributes_and_summary, duration=thisArticle.duration, thumb=thisArticle.thumb, infoLabel=thisArticle.size))
    
    if saveDict:
      Dict[nzbItemsDict] = nzbItems
      #pass

  if (len(dir)+dupesFound)>=nzb.RESULTS_PER_PAGE:
    #Maybe we have more results, since newzbin only returns 100 at a time
    log(4, funcName + "len(dir): " + str(len(dir)) + ", adding an option to go to the next page")
    resultsSoFar = page * nzb.RESULTS_PER_PAGE
    page = page + 1
    dir.Append(Function(DirectoryItem(SearchMovies, "More than " + str(resultsSoFar) + " matches, Next Page"), value=value, title2=title2, maxResults=str(nzb.RESULTS_PER_PAGE), days=str(days), offerExpanded=offerExpanded, expandedSearch=expandedSearch, page=page))

  if offerExpanded:
    dir.Append(Function(DirectoryItem(SearchMovies, "[Expand this search...]"), value=value, title2="[expanded] " + title2, maxResults=str(int(maxResults)*ExpandedSearchMaxResultsFactor), days=str(int(days)*ExpandedSearchTimeFactor), offerExpanded=True, expandedSearch=True))
  #dir.Sort("title2")
  return dir

####################################################################################################
def getTVRage_metadata(tvRageUrl):
  returnDict = {}
  funcName = "[getTVRage_metadata] "
  log(4, funcName + "Getting Metadata for URL: " + tvRageUrl)
  #grab show duration
  #try:
  #  returnDict["duration"] = int(XML.ElementFromURL("http://services.tvrage.com/feeds/showinfo.php?sid=" + tvRageUrl.split('/')[4].replace("id-","")).xpath("//Runtime")[0]) * 60 * 1000
  #except:
  returnDict["duration"] = 60 * 60 * 1000 # use an hour (in seconds) for the duration as a default
  #HTTP.ClearCache()
  #log(7, funcName, 'Cache cleared, doing the http request')
  try:
    tvRageResp = HTTP.Request(tvRageUrl)
    log(7, funcName, 'Request completed, converting to HTML')
    tvRageHTML = str(tvRageResp.content)
    log(7, funcName, 'Converted to HTML, converting to XML')
    #log(8, funcName, 'tvRageHTML:', tvRageHTML)
    tvRageXML = HTML.ElementFromString(tvRageHTML)
    log(7, funcName, 'Converted to HTML, trying to find metadata')
    #log(8, funcName, 'tvRage.XML:', HTML.StringFromElement(tvRageXML))
    log(7, funcName, 'tvRageUrl.count("episodes"):',tvRageUrl.count("episodes"), 'tvRageURL.count("search.php?search="):', tvRageUrl.count("search.php?search="))
    
    #tvRageXML = HTML.ElementFromURL(tvRageUrl, errors="ignore")
    log(7, funcName, 'tvRageUrl.count("episodes"):',tvRageUrl.count("episodes"), 'tvRageURL.count("search.php"):', tvRageUrl.count("search.php?search="))
    if tvRageUrl.count("episodes") > 0 or tvRageUrl.count("search.php?search=") > 0:
      log(7, funcName, 'More than one episodes or search in', tvRageUrl)
      try:
        #summary = tvRageXML.xpath("//tr[@id='ieconn2']/td/table/tr/td/table/tr/td")[0].text_content().split("');")[-1]
        summary = tvRageXML.xpath("//tr[@id='ieconn2']/td/table//table//td")[0].text_content()
        #summary = summary.replace('.Source:', ".\n\nSource:")
        ads = tvRageXML.xpath("//tr[@id='ieconn2']/td/table//table//td//script")
        for ad in ads:
          log(8, funcName, 'summary:', summary)
          log(8, funcName, 'ad:', ad)
          summary = summary.replace(ad.text_content(), '')
        summary = summary.replace('.Source:', ".\n\nSource:")
      except:
        try:
          summary = tvRageXML.xpath("//tr[@id='ieconn3']/td/table//table//td")[0].text_content()
          ads = tvRageXML.xpath("//tr[@id='ieconn3']/td/table//table//td//script")
          for ad in ads:
            log(8, funcName, 'summary:', summary)
            log(8, funcName, 'ad:', ad)
            summary = summary.replace(ad.text_content(), '')
          summary = summary.replace('.Source:', ".\n\nSource:")
        except:
          summary = ""
      log(8, funcName, 'final summary:', summary)
      returnDict["summary"] = summary
      try:
        seriesName = tvRageXML.xpath("//font[@size='3']/b")[0].text_content()
      except:
        seriesName = ""
      returnDict["seriesName"] = seriesName
      try:
        title = tvRageXML.xpath("//meta[@name='description']")[0].get("content").split("@")[0].strip().replace(" Episode","")
      except:
        title = ""
      returnDict["title"] = title
      try:
        (season, episode) = tvRageXML.xpath("//tr[@id='ieconn1']//td[@class='b2']")[1].text.split('x')
      except:
        (season, episode) = ("", "")
      returnDict["season"] = season
      returnDict["episode"] = episode
      try:
        if tvRageXML.xpath("//tr[@id='ieconn1']//td[@class='b1']")[2].text_content().count("Airdate") > 0:
          airDate = tvRageXML.xpath("//tr[@id='ieconn1']//td[@class='b2']")[2].text
        else:
          airDate = tvRageXML.xpath("//tr[@id='ieconn1']//td[@class='b2']")[3].text
      except:
        airDate = ""
      #Trying to format the airDate.  Should not cause any real failures.
      try:
        testAirDate = datetime.strptime(airDate, "%A %B %d, %Y")
        log(4, funcName + "original airdate: \"" + airDate + "\" and my airdate: \"" + testAirDate + "\"")
      except:
        pass
      #returnDict["airDate"] = testAirDate
      returnDict["airDate"] = airDate
      try:
        votes = tvRageXML.xpath("//li[@class='current-rating']")[0].text_content().split(" ")[1].split("/")[0]
      except:
        votes = ""
      returnDict["votes"] = votes
      try:
        #thumb = tvRageXML.xpath("//div[@align='right']/img[@border='0']")[0].get("src")
        thumb = tvRageXML.xpath("//tr[@id='ieconn2']//img")[0].get("src")
        log(6, funcName, 'Got this thumb url:', thumb)
      except:
        thumb = ""
      returnDict["thumb"] = thumb
      #try:
      #  duration = tvRageXML.xpath("id('iconn2')/td/table[2]/tbody/tr/td[1]/table/tbody/tr[8]/td[2]")
  except:
    error = sys.exc_info()
    log(6, funcName, error)
    log(4, funcName, "TVRage lookup failed.")
    returnDict["seriesName"] = ""
    returnDict["summary"] = ""
    returnDict["title"] = ""
    returnDict["season"] = ""
    returnDict["episode"] = ""
    returnDict["airDate"] = ""
    returnDict["votes"] = ""
    returnDict["thumb"] = ""
    return False

  #Log(returnDict)
  return returnDict

def getIMDB_metadata(imdbID,getDuration=True,getSynopsis=True,getThumb=True,getRating=True):
  funcName = "[getIMDB_metadata]"
  returnDict = {}
  respElements = None
  url = "http://www.imdb.com/title/" + imdbID
  try:
    resp = HTTP.Request(url, cacheTime=longCacheTime, immediate=True)
    log(8, funcName, "RequestURL:", url, "... Response:", resp)
  except:
    log(3, funcName, "IMDB page fetch error:", url)
    return returnDict
  if resp == None:
    log(3, funcName, 'No response at', url)
    return returnDict

  log(8, funcName, 'getting duration:', getDuration)
  if getDuration:
    try:
      findStr = "<h5>Runtime:</h5>"
      x = resp.content.find(findStr)
      if x > 0:
        duration = resp[x+len(findStr)+1:resp.find(" min")]
        try:
          duration = duration.split(":")[1].strip()
        except:
          duration = duration.strip()
        duration = duration.replace('<p>\n','')
        duration = int(duration) * 60 * 1000
      else:
        duration = 0
    except:
      duration = 0
    returnDict["duration"] = duration
    log(8, funcName, "duration:", returnDict["duration"])

  log(8, funcName, 'getting synopsis:', getSynopsis)
  if getSynopsis:
    returnDict["desc"] = getIMDB_synopsis(imdbID, resp)
    log(8, funcName, 'synopsis:', returnDict["desc"])
    
  log(8, funcName, 'getting thumb:', getThumb)
  if getThumb:
    if resp.content.count("Poster Not Submitted") == 0:
      respElements = HTML.ElementFromString(resp)
      try:
        #thumb = respElements.xpath("//div[@class='photo']/a/img")[0].get("src")
        #thumb = thumb[:thumb.find("_SX")] + "_SX500_SY500_" + ".jpg"
        thumb = respElements.xpath("//td[@id='img_primary']//img")[0].get("src")
        log(8, funcName, 'thumb:', thumb)
      except:
        log(5, funcName, "Problem with IMDB thumb retrieval.", url)
        thumb = ""
    else:
      thumb = ""
    returnDict["thumb"] = thumb
    log(8, funcName, 'thumb:', returnDict['thumb'])

  log(8, funcName, 'checking rating:', getRating)
  if getRating:
    if resp.content.find("<small>(awaiting") > 0:
      imdbRating = ""
    else:
      if respElements == None:
        respElements = HTML.ElementFromString(resp)
      try:
        imdbRating = respElements.xpath("//div[@class='meta']/b")[0].text.split("/")[0]
      except:
        return returnDict
    returnDict["rating"] = imdbRating
    log(8, funcName, 'rating:', returnDict['rating'])
  #log(7, funcName, 'Returing IMDB Metadata:', returnDict)
  return returnDict

def getIMDB_synopsis(imdbID, imdbTitlePage):
  funcName = '[getIMDB_synopsis]'
  url = "http://www.imdb.com/title/" + imdbID + "/plotsummary"
  plotSummaryExists = False
  #Log(url)
  try:
    resp = HTTP.Request(url, cacheTime=longCacheTime)
    plotSummaryExists = True
  except:
    log(3, funcName, "failed to get imdb plotsummary page:", url)
    
  if plotSummaryExists:
    try:
      desc = HTML.ElementFromString(resp).xpath("//p[@class='plotpar']")[0].text_content()#.encode('utf-8')
      log(8, funcName, 'plot summary desc:', desc)
    except:
      plotSummaryExists = False
  
  if not plotSummaryExists:
    try:
      x = imdbTitlePage.find("<h5>Plot:</h5>")
      if x > 0:
        desc = imdbTitlePage[x+14:imdbTitlePage.find("|",x+15)] #.encode('utf-8')
        desc = HTML.ElementFromString(desc.replace(">more</","></").replace(">full summary</","></"), True).text_content() #.encode("utf-8")
      else:
        desc = ""
    except:
      desc = ""
  log(8, funcName, 'desc:', desc)
  return desc

def tmdb_getMetaData(imdbID):
  funcName = "[tmdb_getMetaData]"
  (th, fa, desc, duration) = ("", "", "", "")
  try:
    searchRes = HTTP.Request("http://api.themoviedb.org/2.1/Movie.imdbLookup/en/xml/a3dc111e66105f6387e99393813ae4d5/" + imdbID)
    if searchRes.content.find("Your query didn't return any results.") == -1 and searchRes.content.find("File Not Found Error") == -1:
      r = HTML.ElementFromString(searchRes).xpath("//movie")[0]
      try:
        th = r.xpath("images/image[@type='poster' and @size='original']")[0].get('url')
      except:
        pass
      try:
        fa = r.xpath("images/image[@type='backdrop' and @size='original']")[0].get('url')
      except:
        pass
      try:
        desc = r.xpath("overview")[0].text #.decode('utf-8','ignore')
      except:
        pass
      try:
        duration = int(r.xpath("runtime")[0].text) * 60 #.decode('utf-8','ignore')
      except:
        pass
  except:
    log(3, funcName, "tmdb connection error, id:", imdbID)
  return {"thumb":th,"fanart":fa,"desc":desc}

def movieposterdb_getThumb(imdbID):
  poster = ""
  try:
    mpdb_dict = JSON.ObjectFromURL("http://api.movieposterdb.com/json.inc.php?imdb=" + imdbID.replace("tt","") + "&width=300")
    if mpdb_dict and not ("errors" in mpdb_dict):
      poster = mpdb_dict["imageurl"] #.encode('utf-8')
      #Log("***" + p)
      #p = ""
  except:
    pass
  finally:
    return poster

####################################################################################################
# General use functions
####################################################################################################

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

####################################################################################################
#Get all the nzbIDs associated with all the entries of the requested title
def getAllEntriesIDs(title, allEntries):
  funcName = "[getAllEntriesIDs]"
  titleEntries = []
  for eachentry in allEntries:
    thisEntryTitle = eachentry.xpath("title")[0].text
    thisEntryID = eachentry.xpath("report:id", namespaces=NEWZBIN_NAMESPACE)[0].text
    if title == thisEntryTitle:
      titleEntries.append(thisEntryID)

  log(4, funcName, "all IDs:", titleEntries)
  return titleEntries