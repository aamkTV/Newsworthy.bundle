from array import *
from common import *
#from PMS import *
#from PMS.Network import *
#from PMS.Plugin import *
from nntpclient import nntpClient
from queue import Queue
from configuration import *

############################################################################################################
# Recently Done
# + Added search by video quality, set in preferences
# + Added the ability to page through the return result set from newzbin (ie. page through >100 results)
# + Added log() function with a loglevel input to clean up the logs, and choose what gets logged and when
#
# + Fixed a bug that caused downloads to fail when the filename had an illegal URL character
# + Fixed a bug where non-rar files were attempting to be unrarred, causing the whole unrar to fail
#   + Added a list of files to not be downloaded (see scrubNZB)
# + Added support for nzb matrix
# - Removed support for newzbin (only from the preferences, underlying code still exists
#
############################################################################################################

#### TO DO
# 1. refactor
# 2. allow for saving the queues over restarts

PREFIX      = "/video/newzworthy"

nzbServiceInfo = NZBService()
app = NewzworthyApp()
nzb = None
nntp = None
loggedInNZBService = False

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

  #setNZBService()

  #global nntp
  #nntp=nntpClient()
  #log(4, funcName, 'NNTP Username, password, host, port, ssl:', nntp.nntpUsername, nntp.nntpPassword, nntp.nntpHost, nntp.nntpPort, nntp.nntpSSL)
  #nntp.connect()

####################################################################################################
def setNZBService():
  funcName='[setNZBService]'
  global nzb
  global loggedInNZBService
  global nzbServiceInfo

  loggedInNZBService = False
  serviceImported=False
  nzb = None
  serviceName=Prefs['NZBService']
  log(4,funcName,'importing NZBService:', serviceName)

  if serviceName=='Newzbin':
    log(4, funcName, 'importing newzbin')
    import newzbin as nzb
    serviceImported=True
    nzbServiceInfo.newzbinUsername = getConfigValue(theDict=nzbConfigDict, key='newzbinUsername')
    log(4, funcName, 'newzbin Username:', nzbServiceInfo.newzbinUsername)
    nzbServiceInfo.newzbinPassword = getConfigValue(theDict=nzbConfigDict, key='newzbinPassword')
    log(4, funcName, 'newzbin Password:', nzbServiceInfo.newzbinPassword)
  elif serviceName=='NZBMatrix':
    log(4, funcName, 'importing nzbmatrix')
    import nzbmatrix as nzb
    serviceImported=True
    log(4, funcName, 'Getting nzbMatrix Username')
    nzbServiceInfo.nzbmatrixUsername = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixUsername')
    log(4, funcName, 'nzbMatrix Username:', nzbServiceInfo.nzbmatrixUsername)
    nzbServiceInfo.nzbmatrixPassword = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixPassword')
    log(4, funcName, 'nzbMatrix Password:', nzbServiceInfo.nzbmatrixPassword)
    #nzbServiceInfo.nzbmatrixAPIKey = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixAPIKey')

  return serviceImported

####################################################################################################
def CreateDict():
  # Create dict objects
  # Dict[nzbItemsDict] = {}
  # Dict[TVFavesDict] = []
  # Dict[nzbConfigDict] = {}
  # Dict[nntpConfigDict] = {}
  # Dict[FSConfigDict] = {}
  pass

####################################################################################################
def CreatePrefs():
  Prefs.Add(id='ShowSDTV', type='bool', default='false', label='TV: Show SD TV Results?')
  Prefs.Add(id='ShowHDTV', type='bool', default='true', label='TV: Show HD (720/1080) TV Results?')
  Prefs.Add(id='consolidateTVDuplicates', type='bool', default='true', label='TV: Consolidate Duplicates Search Results?')
  Prefs.Add(id='ShowNonHDMovies', type='bool', default='false', label='Movies: Show Non-HD Movie Results?')
  Prefs.Add(id='Show720pMovies', type='bool', default='true', label='Movies: Show 720p Movie Results?')
  Prefs.Add(id='Show1080iMovies', type='bool', default='true', label='Movies: Show 1080i Movie Results?')
  Prefs.Add(id='Show1080pMovies', type='bool', default='true', label='Movies: Show 1080p Movie Results?')
  #Prefs.Add(id='ShowBluRayMovies', type='bool', default='false', label='Movies: Show Blu-Ray Movie Results (>25GB)? (No support)')
  Prefs.Add(id='consolidateMovieDuplicates', type='bool', default='true', label='Movies: Consolidate Duplicate Search Results?')
  Prefs.Add(id='ShowSearchByNewzbinID', type='bool', default='false', label="General: Do you want to be able to search by NewzbinID?")
  Prefs.Add(id='NZBService', type='enum', values=['NZBMatrix', 'Newzbin'], default='NZBMatrix', label="Which NZB service do you use?")
  Prefs.Add(id='ShowDiags', type='bool', default='false', label="Show troubleshooting options?  (Advanced Users Only)")
  #Prefs.Add(id='OfferAlternateVideoQuality', type='bool', default='false', label="General: Offer more video quality options during search?")

####################################################################################################
def ValidatePrefs():
  funcName = "[ValidatePrefs] "
  log(2, funcName + "Validating Preferences and reloading main menu")
  setNZBService()
  global loggedInNZBService
  loggedInNZBService = False
  loggedInNZBService = nzb.performLogin(nzbServiceInfo, forceRetry=True)
  
  global app
  app = NewzworthyApp()

####################################################################################################
def RestartNW(sender, key):
  Plugin.Restart()
  
####################################################################################################
def MainMenu():
  funcName = '[MainMenu]'
  
  # Set the right NZB servers to use
  if not loggedInNZBService:
    global nzbServiceInfo
    global loggedInNZBService
    # try to log into the NZB Service...
    setNZBService()
    loggedInNZBService = nzb.performLogin(nzbServiceInfo, forceRetry=True)
    log(3, funcName + "Login success:", str(loggedInNZBService))
  else:
    log(3, funcName + "Already logged in")

  # Empty context menu, since there aren't any useful contextual options right now.
  cm = ContextMenu(includeStandardItems=False)
  cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
  dir = MediaContainer(contextMenu=cm, noCache=True, viewGroup="Lists")

  # Sub-menu for TV
  if loggedInNZBService:
    log(5, funcName, 'Logged in, showing TV & Movie menu options')
    dir.Append(Function(DirectoryItem(BrowseTV, title=("Go to TV"), contextKey="a", contextArgs={})))
    # Sub-menu for Movies
    dir.Append(Function(DirectoryItem(BrowseMovies, title=("Go to Movies"), contextKey="a", contextArgs={})))
    # Special case just for searching by newzbinID
    if(bool(Prefs['ShowSearchByNewzbinID']) and Prefs['NZBService']=="Newzbin"):
      dir.Append(Function(InputDirectoryItem(Search, title=("Search by Newzbin ID"), prompt=("Search by Newzbin ID"), thumb=R('search.png'), contextKey="a", contextArgs={}), category="99"))
  else:
    log(5, funcName, 'Not logged in, showing option to update preferences')
    dir.Append(Function(DirectoryItem(RestartNW, title=("Not logged in to " + Prefs["NZBService"]), contextKey="a", contextArgs={}), key="a"))

  # Show the troubleshooting options.  Not recommended, but can be very useful.
  if bool(Prefs['ShowDiags']):
    log(4, funcName, 'Showing diagnostic menu options')
    log(5, funcName, 'Showing "Clear the cache"')
    dir.Append(Function(DirectoryItem(clearArticleDict, title="Clear the cache", contextKey="a", contextArgs={})))
    #put in a way to clear the SAB queue
    #dir.Append(Function(DirectoryItem(action_deleteQueue, title="Clear the SAB Download Queue", contextKey="a", contextArgs={})))
    log(5, funcName, 'Showing "Show All Dicts"')
    dir.Append(Function(DirectoryItem(showAllDicts, title="Show All Dicts", contextKey="a", contextArgs={})))
  else:
    log(4, funcName, 'NOT showing (ie. hiding) diagnostic menu options')

  # Show the preferences option
  log(5, funcName, 'Showing Preferences')
  dir.Append(PrefsItem(L("Preferences"), contextKey="a", contextArgs={}))
  log(5, funcName, 'Showing setup options')
  dir.Append(Function(DirectoryItem(configure, title="Setup servers, usernames, and passwords", contextKey="a", contextArgs={})))
  log(5, funcName, 'Showing Manage Queue')
  dir.Append(DirectoryItem(Route(manageQueue), title="Manage Queue"))
  log(5, funcName, 'Show Dir')
  return dir

####################################################################################################
def clearArticleDict(sender):
  funcName = "[clearArticleDict]"
  log(1, funcName, 'articleDict before clearing:', Dict[nzbItemsDict])
  Dict[nzbItemsDict] = {}
  log(1, funcName, 'articleDict after clearing:', Dict[nzbItemsDict])
  #MainMenu()

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
      log(5, funcName, str(thisDict), 'not a dict type, assuming it''s a list')
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
  dir = MediaContainer(contextMenu=cm, noCache=True, title2="TV")

  if nzb.supportsGenres(): dir.Append(Function(DirectoryItem(BrowseTVGenres,         title=("Browse Recent TV by Genre"), contextKey="a", contextArgs={}), filterBy="Video Genre"))
  dir.Append(Function(InputDirectoryItem(Search,     title=("Search TV"), prompt=("Search TV"), thumb=R('search.png'), contextKey="a", contextArgs={}), category="8"))
  #dir.Append(Function(DirectoryItem(BrowseTVFavorites,	title=("Browse TV Favorites (12 hours)"), contextKey="a", contextArgs={}), days=".5"))
  dir.Append(Function(DirectoryItem(BrowseTVFavorites,	title=("Browse TV Favorites (1 Day)"), contextKey="a", contextArgs={}), days="1"))
  dir.Append(Function(DirectoryItem(BrowseTVFavorites,	title=("Browse TV Favorites (1 Week)"), contextKey="a", contextArgs={}), days="7"))
  dir.Append(Function(DirectoryItem(BrowseTVFavorites,	title=("Browse TV Favorites (1 Month)"), contextKey="a", contextArgs={}), days="30"))
  dir.Append(Function(DirectoryItem(BrowseTVFavorites,	 title=("Browse TV Favorites (All)"), contextKey="a", contextArgs={}), days="0"))
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
  log(4, funcName + "Current contents of " + TVFavesDict + ": " + str(faves))

  #Add a contextual menu to each item to remove it from the favorites
  if len(faves) >= 1:
    cm = ContextMenu(includeStandardItems=False)
    cm.Append(Function(DirectoryItem(RemoveTVFavorite, title='Remove')))
  else:
    cm = ContextMenu(includeStandardItems = False)
    cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))


  #Instantiate the list...
  dir = MediaContainer(contextMenu=cm, noCache=True, replaceParent=False, noHistory=True)

  #Add a static item as an option to add new favorites
  dir.Append(Function(InputDirectoryItem(AddTVFavorite, title=L("Add a new Favorite"), prompt=L("Add a new Favorite"), thumb=R('search.png'), contextKey="a", contextArgs={})))
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
  
  try:
    log(4, funcName, 'Retrieved these favorites:',faves)
    query = nzb.concatSearchList(faves)

    log(3, funcName + "query: " + query)
    dir = SearchTV(sender, value=query, title2="Favorites", days=days)
    return dir
  except:
    return MessageContainer("No favorites", "You have not saved any favorite TV shows to search.  Add some favorites and then try again.")

####################################################################################################
def SearchTV(sender, value, title2, days=TVSearchDays_Default, maxResults=str(0), offerExpanded=False, expandedSearch=False, page=1, invertVideoQuality=False, allOneTitle=False):
  funcName = "[SearchTV] "

  # Determine if we will be consolidating duplicates to a single entry
  if allOneTitle:
    consolidateDuplicates = False
  else:
    consolidateDuplicates = bool(Prefs['consolidateTVDuplicates'])

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

  dir = MediaContainer(viewGroup='Details', title2=thisTitle, noCache=True)

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
              if thisArticle.moreInfoURL.count("episodes") > 0: #don't mess with whole season dvd rips
                log(4, funcName, 'found more than 0 episodes in the url:', thisArticle.moreInfoURL)
                tvRageDict = getTVRage_metadata(thisArticle.moreInfoURL)
                thisArticle.title = tvRageDict["title"]
                thisArticle.summary = thisArticle.size + "\n\n" + tvRageDict["summary"]
                thisArticle.subtitle = "S" + tvRageDict["season"] + "E" + tvRageDict["episode"] + " (" + tvRageDict["airDate"] + ")"
                thisArticle.rating = tvRageDict["votes"]
                thisArticle.thumb = tvRageDict["thumb"]
                thisArticle.duration = tvRageDict["duration"]
              else:
                log(4, funcName, 'Did not find keyword "episodes" in', thisArticle.moreInfoURL, 'for:', thisArticle.title)
            else:
              log(5, funcName, 'No TVRageURL found for:', thisArticle.title)


            log(4, funcName, "Adding \"" + thisArticle.title + "\" to the dir")
            articleItem = Function(DirectoryItem(Article, thisArticle.title, thisArticle.subtitle, summary=thisArticle.summary, duration=thisArticle.duration, thumb=thisArticle.thumb, rating=thisArticle.rating, infoLabel=thisArticle.size), theArticleID=thisArticle.nzbID) #title2=title, fanart=fanart, thumb=thumb, rating=rating, duration=duration)

            # Add the item to the persistent-ish cache
            nzbItems[thisArticle.nzbID] = thisArticle
            saveDict = True
            dir.Append(articleItem)

          else: # The nzbID is already in the dict, therefore we can just pull it from cache
            log(4, funcName, "Cached: Adding \"" + nzbItems[thisArticle.nzbID].title + "\" from the cache.")
            dir.Append(Function(DirectoryItem(Article, thisArticle.title, thisArticle.subtitle, summary=thisArticle.summary, duration=thisArticle.duration, thumb=thisArticle.thumb, rating=thisArticle.rating, infoLabel=thisArticle.size), theArticleID=thisArticle.nzbID))

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
    #log(4, funcName, 'Saving Dict:', nzbItemsDict)
    #Dict[nzbItemsDict] = nzbItems
    pass
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
def Article(sender, theArticleID='', theArticle='nothing', title2='', dirname='', subtitle='', thumb='', fanart='', rating='', summary='', duration=''):
  funcName="[Article]"
  
  if theArticle=='nothing' and not theArticleID=='':
    nzbItems = Dict[nzbItemsDict]
    theArticle=nzbItems[theArticleID]
  
  #Determine what you want to show as the secondary window title
  if theArticle.mediaType=='TV':
    log(4, funcName, theArticle.title, "is a TV show")
    title2 = "TV > " + theArticle.title
  elif theArticle.mediaType=='Movie':
    log(4, funcName, theArticle.title, "is a Movie")
    title2 = "Movies > " + theArticle.title
  else:
    log(4, funcName, theArticle.title, "is an unknown media type (i.e. not a TV show nor a movie")
    title2 = theArticle.title

  dir = MediaContainer(viewGroup='Details', title2=title2, noCache=True, autoRefresh=5)
  try:
    if theArticle.fanart != "":
      dir.art = theArticle.fanart
  except:
    pass

  #art = Function(DirectoryItem(StupidUselessFunction, subtitle=theArticle.subtitle))
  dir.Append(Function(DirectoryItem(AddReportToQueue, "Add To Download Queue"), nzbID=theArticle.nzbID))
  
  if app.queue.items >= 1:
    dir.Append(DirectoryItem(Route(manageQueue), title="Manage Queue"))

  #dir.Append(addToQueue)
  return dir

####################################################################################################
def AddReportToQueue(sender, nzbID, article='nothing'):
  funcName = "[AddReportToQueue]"
  #global app
  log(5, funcName, 'Setting queue object, should be using previously initialized app object''s queue')
  queue = app.queue
  log(5, funcName, 'queue object set')
  if article=='nothing':
    nzbItems = Dict[nzbItemsDict]
    article = nzbItems[nzbID]
  item = queue.add(nzbID, nzb, article)
  item.download()
  log(5, funcName, 'Items queued:', len(app.queue.items))
  header = 'Item queued'
  message = '"%s" has been added to your queue' % item.report.title
  return MessageContainer(header, message)

####################################################################################################
@route('/video/newzworthy/manageQueue')
def manageQueue():
  funcName = "[manageQueue]"

  # First check if there's anything in the queue
  log(5, funcName, 'Items in queue:', len(app.queue.items))
  if len(app.queue.items) == 0:
    return MessageContainer('Nothing in queue', 'There are no items in the queue')

  # Display the contents of the queue
  log(5, funcName, 'Creating dir')
  dir = MediaContainer(viewGroup="Details", noCache=True, autoRefresh=5)
  log(5, funcName, 'Looking at each item in queue')
  for item in app.queue.items:
    subtitle = ' '
    summary = ' '
    log(6, funcName, 'Examining:', item.report.title)
    if item.complete:
      log(6, funcName, 'item.complete:', item.complete)
      subtitle = L("DL_COMPLETE")
      summary = ''

    elif item.play_ready:
      log(6, funcName, 'item.play_ready:', item.play_ready)
      subtitle = L("DL_PLAY_READY")
      summary = ''

    elif item.downloading:
      log(6, funcName, 'item.downloading:', item.downloading)
      tm = item.play_ready_time
      log(6, funcName, 'item.play_ready_time:', item.play_ready_time)
      # All these strings can be found in the Strings folder of the bundle
      if tm == 0:
        subtitle = L('DL_PLAY_READY')
        summary = ''
      else:
        subtitle = L('DL_DOWNLOADING')
        if tm < 5:
          summary = L('DL_SUM_PR_FEW_SECS')
        elif tm > 60:
          mins = tm / 60
          secs = tm % 60
          if mins == 1:
            key = 'DL_SUM_PR_MIN_SECS'
          else:
            key = 'DL_SUM_PR_MINS_SECS'
          summary = F(key, mins, secs)
        else:
          summary = F('DL_SUM_PR_SECS', tm)

    else:
      subtitle = L('DL_QUEUED')
    log(5, funcName, 'Queue item:', item.report.title+': subtitle:', subtitle, 'summary:', summary)
    log(5, funcName, 'Found in queue:', item)
    dir.Append(
      PopupDirectoryItem(
        Route(QueueItemPopup, id=item.id),
        title=item.report.title,
        subtitle=subtitle,
        summary=summary
        )
      )

  return dir

####################################################################################################
@route('/video/newzworthy/queue/{id}')
def QueueItemPopup(id):
  c = MediaContainer()

  for item in app.queue.items:
    if item.id == id: break
    else: item = None

  if not item: return

  if item.play_ready:
    c.Append(
      VideoItem(
        Route(StartStreamAction, id=item.id),
        title = L('PLAY_DL')
      ))

  if not item.complete:
    f = CancelDownloadAction
    title_key = 'CANCEL_DL'
  else:
    f = RemoveItemAction
    title_key = 'REMOVE_DL'

  c.Append(
    DirectoryItem(
      Route(f, id=item.id),
      title = L(title_key)
    ))

  return c

####################################################################################################
# These functions are related specifically to the queue
####################################################################################################

@route('/video/newzworthy/queue/{id}/play')
def StartStreamAction(id):
  for item in app.queue.items:
    if item.id == id: break
    else: item = None

  if not item: return
  if item.play_ready:
    return Redirect(item.stream)

@route('/video/newzworthy/pauseDownload')
def pauseDownload():
  funcName = "[pauseDownload]"
  log(5, funcName, "Pausing downloader client tasks")
  app.downloader.stop_download_thread()
  return True

@route('/video/newzworthy/queue/{id}/cancel')
def CancelDownloadAction(id):
  funcName = "[CancelDownloadAction]"
  log(5, funcName, "Shutting down downloader client tasks")
  # Stop (Pause) the download thread
  app.downloader.stop_download_thread()
  # Get the item so you can remove it from all the queues
  item = app.queue.getItem(id)
  if item.downloading:
    # Remove the item from the download queue
    app.downloader.item_queue.remove(item)
  # Remove the item from the queue
  app.queue.items.remove(id)

  log(5, funcName, "Restarting download client tasks")
  app.downloader.start_download_thread()
  return True


@route('/video/newzworthy2/queue/{id}/remove')
def RemoveItemAction(id):
  funcName = "[RemoveItemAction]"
  log(5, funcName, "Removing id", id, "from the queue")
  for item in app.queue.items:
    if item.id == id:
      app.queue.items.remove(item)
      log(5, funcName, "Done removing id", id, "from the queue")
      break
  return True

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
    title = XML.ElementFromString(newzbinHtml, True).xpath("//table[@class='dataIrregular']//tr//td")[0].text_content() #.encode('utf-8')
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
  filterHTML = HTTP.Request(NEWZW_SEARCH_URL)
  for genre in XML.ElementFromString(filterHTML, True, cacheTime=CACHE_INTERVAL).xpath('//optgroup[@label="' + filterBy + '"]/option'):
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
  for genre in XML.ElementFromString(filterHTML, True).xpath('//optgroup[@label="' + filterBy + '"]/option'):
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
              thisArticle.imdbDict = getIMDB_metadata(thisArticle.moreInfo)
              thisArticle.tmdbDict = tmdb_getMetaData(thisArticle.moreInfo)
              thisArticle.mpdbThumb = movieposterdb_getThumb(thisArticle.moreInfo)
              try:
                thisArticle.description = imdbDict["desc"] #.encode('utf-8')
                try:
                  if thisArticle.description == "":
                    thisArticle.description = tmdbDict["desc"]
                except:
                  pass
              except:
                pass
              try:
                thisArticle.thumb = imdbDict["thumb"]
                if thisArticle.thumb == "":
                  thisArticle.thumb = mpdbThumb
                  if thisArticle.thumb == "":
                    thisArticle.thumb = tmdbDict["thumb"]
              except:
                pass
              try:
                thisArticle.duration = str(int(imdbDict["duration"]))
              except:
                pass
              try:
                thisArticle.fanart = tmdbDict["fanart"]
              except:
                pass
              try:
                thisArticle.rating = imdbDict["rating"]
              except:
                thisArticle.rating = ""

#            articleItem = Function(DirectoryItem(Article, thisArticle.title, subtitle=thisArticle.reportAge, summary=thisArticle.description, duration=thisArticle.duration, thumb=thisArticle.thumb, infoLabel=thisArticle.size), newzbinID=thisArticle.nzbID, title2=thisArticle.title, fanart=thisArticle.fanart, thumb=thisArticle.thumb, rating=thisArticle.rating, duration=thisArticle.duration)

            nzbItems[thisArticle.nzbID] = thisArticle
            saveDict = True
          else:
            log(4, funcName + "Pulling item from cache")
            thisArticle = nzbItems[thisArticle.nzbID]
            #Log("Pulled article from cache.")

          articleItem = Function(DirectoryItem(Article, thisArticle.title, subtitle=thisArticle.reportAge, summary=thisArticle.description, duration=thisArticle.duration, thumb=thisArticle.thumb, infoLabel=thisArticle.size), theArticleID=thisArticle.nzbID)

          if thisArticle.fanart != "":
            dir.art = ""
            articleItem.art = thisArticle.fanart

          dir.Append(articleItem)
    if saveDict:
      #Dict[nzbItemsDict] = nzbItems
      pass

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
  try:
    tvRageXML = XML.ElementFromURL(tvRageUrl, True, errors="ignore")
    if tvRageUrl.count("episodes") > 0:
      try:
        summary = tvRageXML.xpath("//tr[@id='ieconn2']/td/table/tr/td/table/tr/td")[0].text_content().split("');")[-1]
      except:
        try:
          summary = tvRageXML.xpath("//tr[@id='ieconn3']/td/table/tr/td/table/tr/td")[0].text_content().split("');")[-1]
        except:
          summary = ""
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
        thumb = tvRageXML.xpath("//div[@align='right']/img[@border='0']")[0].get("src")
      except:
        thumb = ""
      returnDict["thumb"] = thumb
      #try:
      #  duration = tvRageXML.xpath("id('iconn2')/td/table[2]/tbody/tr/td[1]/table/tbody/tr[8]/td[2]")
  except:
    Log("TVRage lookup failed.")
    returnDict["seriesName"] = ""
    returnDict["summary"] = ""
    returnDict["title"] = ""
    returnDict["season"] = ""
    returnDict["episode"] = ""
    returnDict["airDate"] = ""
    returnDict["votes"] = ""
    returnDict["thumb"] = ""

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
    #print("IMDB page fetch error")
    #Log(url)
    return returnDict
  if resp == None:
    #Log(url)
    return returnDict

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

  if getSynopsis:
    returnDict["desc"] = getIMDB_synopsis(imdbID, resp)
    #Log(returnDict["desc"])
  if getThumb:
    if resp.content.count("Poster Not Submitted") == 0:
      respElements = HTML.ElementFromString(resp)
      try:
        thumb = respElements.xpath("//div[@class='photo']/a/img")[0].get("src")
        thumb = thumb[:thumb.find("_SX")] + "_SX500_SY500_" + ".jpg"
      except:
        Log("Problem with IMDB thumb retrieval.")
        thumb = ""
    else:
      thumb = ""
    returnDict["thumb"] = thumb

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
  return returnDict

def getIMDB_synopsis(imdbID, imdbTitlePage):
  url = "http://www.imdb.com/title/" + imdbID + "/plotsummary"
  #Log(url)
  try:
    resp = HTTP.Request(url, cacheTime=longCacheTime)
  except:
    Log("failed to get imdb plotsummary page")
    return ""
  try:
    desc = HTML.ElementFromString(resp).xpath("//p[@class='plotpar']")[0].text #.encode('utf-8')
  except:
    try:
      x = imdbTitlePage.find("<h5>Plot:</h5>")
      if x > 0:
        desc = imdbTitlePage[x+14:imdbTitlePage.find("|",x+15)] #.encode('utf-8')
        desc = HTML.ElementFromString(desc.replace(">more</","></").replace(">full summary</","></"), True).text_content() #.encode("utf-8")
      else:
        desc = ""
    except:
      desc = ""
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
