import re
import sys
from common import *

name = 'NZBMatrix'
SEARCH_URL = 'https://api.nzbmatrix.com/v1.1/search.php?'
#NZBM_ROOT = 'http://nzbmatrix.com/nzb.php?category=Movies&sort=1&type=asc&page=0'
#NZBM_BASE = 'http://nzbmatrix.com'
#NZBM_ERRORS = {'error:invalid_login':'There is a problem with the username you have provided.', 'error:invalid_api':'There is a problem with the API Key you have provided.', 'error:invalid_nzbid':'There is a problem with the NZBid supplied.', 'error:please_wait_':'Please wait before retry.', 'error:vip_only':'You need to be VIP or higher to access.', 'error:disabled_account':'User Account Disabled.', 'error:no_nzb_found':'No NZB found.'}
#NZBM_ERRORS2 = {'error:x_daily_limit':'You have reached the daily download limit of x.'}

langFilter = "englishonly=1"
sortFilter = "sort=0&type=asc"
CACHE_TIME = 30 # seconds
RESULTS_PER_PAGE = 50
CAT_TV = "tv-all"
CAT_MOVIES = "movies-all"
HTTP_TIMEOUT = 60

MOVIE_BROWSING = True
TV_BROWSING = True
TV_SEARCH = True
MOVIE_SEARCH = True

LoggedIn = False

####################################################################################################
def performLogin(nzbService, forceRetry=False):
  funcName = '[nzbmatrix.performLogin]'

  url = 'http://api.nzbmatrix.com/v1.1/account.php?username=%s&apikey=%s'
  if nzbService.nzbmatrixUsername != "" and nzbService.nzbmatrixAPIKey != "": # and nzbService.nzbmatrixPassword != "":
    USERNAME = nzbService.nzbmatrixUsername
    APIKEY = nzbServiceInfo.nzbmatrixAPIKey
    url = url %(USERNAME, APIKEY)
    log(9, funcName, 'url:', url)

    if forceRetry:
      log(3, funcName, 'Forcing the login retry, clearing the cache')
      HTTP.ClearCache()

    try:
      #HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/533.21.1 (KHTML, like Gecko) Version/5.0.5 Safari/533.21.1'
      rsp = HTTP.Request(url=url, immediate=True, timeout=HTTP_TIMEOUT)
      log(5, funcName, 'nzbmatrix login response received')
      response = rsp.content
      log(9, funcName, 'response string:', response)
      try:
        if response.index("USERNAME") != -1:
          return True
        else:
          return False
      except:
        log(4, funcName, 'Error checking for successful login:', sys.exc_info()[1])
        return False      
    except Ex.URLError, e:
      log(4,funcName, "URL Error:", e.reason)
      return False
  else:
    log(4, funcName, 'NZBMatrix username/apikey not specified')
    return False

####################################################################################################
def supportsGenres():
  return False

####################################################################################################
def search(category, query_list, period, page):
  funcName = '[nzbmatrix.search]'
  
  if len(query_list)>0 and query_list[0]<>'':
    query_values = concatSearchList(query_list)
  else:
    query_values = ''
  

  if page>1:
    log(4, funcName, 'page:', page)
    offset = "&offset=" + str(((page-1)*RESULTS_PER_PAGE))
  else:
    log(4, funcName, 'page is <1:', page)
    offset = ''
    
  # Add any video format filters
  if category == CAT_TV:
    VideoFilters = getTVVideoFilters()
    LanguageFilters = getTVLanguages()
  elif category == CAT_MOVIES:
    VideoFilters = getMovieVideoFilters()
    LanguageFilters = getMovieLanguages()
  if len(VideoFilters)>0: query_values += " " + VideoFilters
  if len(LanguageFilters)>0: query_values += LanguageFilters

  nzbmatrixUsername = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixUsername')
  nzbmatrixAPIKey = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixAPIKey')
  
  url = SEARCH_URL + "search=" + String.Quote(query_values,usePlus=False) + "&catid=" + category + "&age=" + period + "&num=" + str(RESULTS_PER_PAGE) + "&searchin=name" + offset + "&username=" + nzbmatrixUsername + "&apikey=" + nzbmatrixAPIKey

  log(3, funcName + "URL: " + url)
  #testresp = HTTP.Request(url)
  #log(4, funcName, "http response:",testresp)
  #allResults = XML.ElementFromURL(url, isHTML=True, cacheTime=CACHE_TIME).xpath('//table[@class="nzbtable grid"]//tr[@class!="nzbtable_head"]')
  try:
    #global cookie
    #log(9, funcName, 'Setting cookie to:', cookie)
    #HTTP.Headers['cookie'] = cookie
    response = HTTP.Request(url, timeout=HTTP_TIMEOUT)
    headers = response.headers
    log(9, funcName, 'Response Headers:', headers)
    log(9, funcName, 'Response content:', response.content)
    allResults = response.content.split("|")
    # hack because the last entry is not a real item
    t = allResults.pop()
    if len(t) >= 10:
      log(7, funcName, 'Did not remove last allResults entry:', t)
      allResults.append(t)
    else:
      log(7, funcName, 'Removed blank entry from allResults')
  except Ex.URLError, e:
    log(1, funcName, 'Error querying:', e.reason)
    raise
  except:
    log(1, funcName, 'Error searching:', sys.exc_info()[1])
    raise

  allEntries = []
  log(5,funcName,'Getting Dict:',nzbItemsDict)
  nzbItems = Dict[nzbItemsDict]
  log(8,funcName, 'Got Dict:',nzbItemsDict,nzbItems)
#  log(7, funcName, 'allresults:', allResults)
  if len(allResults)>0:
    @parallelize
    def processAllNZBEntries():

      for entry in allResults:

        @task
        def processNZBEntry (entry=entry):
          entryCached = False
          thisEntry = article()
          outputs = entry.replace("; ", ";").split(";")
          values = {}
          for output in outputs:
            if len(output) >= 3:
              try:
                nm, val = output.split(":", 1) #Split only once.  Needed due to time formattting in the field.
                if nm.find('\n') == 0: nm = nm[1:]
                values[nm] = val
              except:
                log(3, funcName, 'unable to read value:', output)
          
          log(7, funcName, 'Values:', values)
            
          try:
            thisEntry.nzbID = values['NZBID']
            thisEntry.newzbinID = thisEntry.nzbID
            if thisEntry.nzbID in nzbItems:
              log(5, funcName, 'key found!')
              thisEntry = nzbItems[thisEntry.nzbID]
              entryCached = True

            if not entryCached or len(thisEntry.title) <= 1:
              thisEntry.title = values['NZBNAME']
              #cleanName = removeExtraWords(thisEntry.title)
              #if cleanName:
              #  thisEntry.title = cleanName
            
            if not entryCached or len(thisEntry.size) <= 1: thisEntry.size = values['SIZE']
            thisEntry.reportAge = "Indexed: " + str(Datetime.ParseDate(values['INDEX_DATE']))
            if not entryCached or (len(thisEntry.moreInfoURL) <=1 and len(thisEntry.moreInfo) <=1):
              if category == CAT_TV: thisEntry.moreInfoURL = values['WEBLINK']
              if category == CAT_MOVIES: thisEntry.moreInfo = getIMDBid(values['WEBLINK'])             

            if category == CAT_TV:
              # Why bother if it's already cached?
              if not entryCached and len(thisEntry.moreInfoURL) <=1:
                log(5, funcName, 'finding TVRageURL for', thisEntry.title)
                cleanName = removeExtraWords(thisEntry.title)
                if len(cleanName) > 1:
                  thisEntry.moreInfoURL = getTVRageURL(cleanName) #TVRageURL
              else:
                log(4, funcName, 'Adding TV Show', thisEntry.title, 'from the cache')

            elif category == CAT_MOVIES:
              if entryCached: log(4, funcName, 'Adding Movie', thisEntry.title, 'from the cache')

            log(5, funcName, 'moreInfoURL:',thisEntry.moreInfoURL, 'moreInfo:', thisEntry.moreInfo)

            # Get the download size in MB
            if not entryCached or thisEntry.sizeMB<=1:
              thisEntry.sizeMB = convert_bytes(thisEntry.size)
              if len(thisEntry.sizeMB) > 1: thisEntry.size = thisEntry.sizeMB
              log(6, funcName, 'start size:', thisEntry.size, ', size in mb:', thisEntry.sizeMB)
            allEntries.append(thisEntry)
          except:
            log(1, funcName, 'Error:', sys.exc_info()[1], '\nValues:', entry)

  return allEntries

####################################################################################################
def getIMDBid(link):
  funcName = "[nzbmatrix.getIMDBid]"
  imdbID = ''

  try:
    log(9, funcName, 'Looking for imdbID in string:', link)
    tokens = link.split("/")
    for val in tokens:
      #log(9, funcName, 'Analyzing this token for imdbID:', val)
      if re.match("tt[0-9]{4,8}", val):
        imdbID = str(val)
        break
  except:
    log(3, funcName, 'Error getting imdb id for', link, 'Error:', sys.exc_info()[1])
  log(4,funcName, 'imdbID:', imdbID)
  return imdbID
####################################################################################################
def getTVRageURL(searchValue):

  funcName = '[nzbmatrix.getTVRageURL]'
  location = ''

  searchURL = "http://www.tvrage.com/search.php?search=" + encodeText(searchValue)
  return searchURL
####################################################################################################
def removeExtraWords(value):
  funcName = '[nzbmatrix.removeExtraWords]'

  cleanName = ""
  infoFound = False
  #numPeriods = value.count(".")
  #numUnderScores = value.count("_")
  #numSpaces = value.count(" ")
  sepChar=" "

  #if numSpaces > numUnderScores and numSpaces > numPeriods: sepChar=" "
  #if numPeriods > numUnderScores and numPeriods > numSpaces: sepChar="."
  #if numUnderScores > numPeriods and numUnderScores > numSpaces: sepChar="_"
  tokens=value.split(sepChar)

  for val in tokens:
    if not infoFound:
      log(6, funcName, 'checking the token "' + val + '"')
      #if re.match("S[0-9][0-9]E[0-9][0-9]", val):
      if re.match("(?i)S?\d\d?[(?i)E|x]\d\d?", val):
        log(6, funcName, 'match found on',val)
        cleanName += " " + val
        infoFound=True
        break
      else:
        if len(cleanName) < 1:
          cleanName += val
        else:
          cleanName += " " + val

  if not infoFound: cleanName = ""

  log(4, funcName, 'Name:"' + value + '" and my cleanName:', cleanName)
  return cleanName

####################################################################################################
def downloadNZBUrl(nzbID):
  funcName = '[nzbmatrix.downloadNZBUrl]'
  downloadURL = "http://nzbmatrix.com/nzb-download.php?id=" + nzbID + "&nozip=1"
  log(4, funcName, 'NZB Download URL:', downloadURL)
  return downloadURL

####################################################################################################
def getArticleSummary(nzbID):
  funcName = '[nzbmatrix.getArticleSummary]'
  postSummary = ''
  return postSummary

####################################################################################################
def concatSearchList(thelist):
  funcName = "[nzbmatrix.concatSearchList]"
  
  query_start = "+("

  query = query_start
  for title in thelist:
    log(4, funcName + "adding '" + title + "' to the query")
    if title.find("-") >=0:
      title = title.replace("^", '')
    else:
      title = "\"" + title.replace("^", '') + "\""
    if len(query)==len(query_start):
      query+="(" + title + ")"
    else:
      query+=" (" + title + ")"
  query+=")"
  log(4, funcName + "query: " + query)

  return query

####################################################################################################
def getTVVideoFilters():
  funcName = "[getTVVideoFilters]"
  HDVideoAttrs = "((720p) (1080i) (1080p))"
  TVHDVideoAttributes = "+" + HDVideoAttrs
  TVSDVideoAttributes = "-" + HDVideoAttrs
  #TVHDVideoAttributes = "(720p or 1080i or 1080p)"
  videoFilter = ""
  # Check which TV Formats to include
  log(4, funcName, 'Getting TVVideoPreferences')
  ShowHD = (Prefs['ShowHDTV'])
  ShowSD = (Prefs['ShowSDTV'])
  log(3, funcName + "ShowSDTV: " + str(ShowSD) + " and ShowHDTV: " + str(ShowHD))
  # We are only covering the use cases where someone wants to intentionally filter by HD/SD content.
  # If both are set to true, no need to filter
  # If both are set to off, I'm assuming there's an error and will display all content

  if ((ShowHD) and not (ShowSD)):
    log(4, funcName + "Show only HD TV")
    videoFilter = TVHDVideoAttributes
  elif ((ShowSD) and not (ShowHD)):
    log(4, funcName + "Show only SD TV")
    videoFilter = TVSDVideoAttributes

  return videoFilter

####################################################################################################
def getMovieVideoFilters():
  funcName = "[getMovieVideoFilters]"
  MovieFormat = ""

  #Check which formats to include
  log(6, funcName, "Checking which formats to include")
  ShowNonHD = (Prefs['ShowNonHDMovies'])
  Show720p = (Prefs['Show720pMovies'])
  Show1080i = (Prefs['Show1080iMovies'])
  Show1080p = (Prefs['Show1080pMovies'])
  #ShowBluRay = (Prefs['ShowBluRayMovies'])

  # Easy use case: All formats to be displayed, no more processing needed
  if (ShowNonHD and Show720p and Show1080i and Show1080p):
    log(3, funcName, "All video formats selected, done")
    return MovieFormat

  MovieIncludeFormat = ""
  MovieExcludeFormat = ""
  Attr720p = "720p"
  Attr1080p = "1080p"
  Attr1080i = "1080i"
  #AttrBluRay = "a:VideoF~Blu-Ray"

  listOfIncludes = []
  listOfExcludes = []

  # Look at each video preference and decide if we're going to include it or exclude it
  if (Show720p):
    listOfIncludes.append(Attr720p)
  else:
    listOfExcludes.append(Attr720p)

  if (Show1080i):
    listOfIncludes.append(Attr1080i)
  else:
    listOfExcludes.append(Attr1080i)

  if (Show1080p):
    listOfIncludes.append(Attr1080p)
  else:
    listOfExcludes.append(Attr1080p)

  #if (ShowBluRay):
  #  listOfIncludes.append(AttrBluRay)
  #else:
  #  listOfExcludes.append(AttrBluRay)

  log(4, funcName + "Selected movie video formats: " + str(listOfIncludes))
  log(4, funcName + "Excluded movie video formats: " + str(listOfExcludes))

  if (len(listOfIncludes) >=1):
    for format in listOfIncludes:
      if(len(MovieIncludeFormat)<=1):
        MovieIncludeFormat += "+(" + format
      else:
        MovieIncludeFormat += " or " + format
    MovieIncludeFormat+= ")"

  log(3, funcName + "MovieIncludeFormat string: " + MovieIncludeFormat)

  if (len(listOfExcludes) >=1):
    for format in listOfExcludes:
      if(len(MovieExcludeFormat)<=1):
        MovieExcludeFormat += "-(" + format
      else:
        MovieExcludeFormat += " or " + format
    MovieExcludeFormat += ")"

  log(3, funcName + "MovieExcludeFormat string: " + MovieExcludeFormat)

  if (not(ShowNonHD)):
    log(4, funcName + "Don't show non-HD movies")
    #MovieFormat = "(" + MovieIncludeFormat + " " + MovieExcludeFormat + ")"
    MovieFormat = MovieIncludeFormat + " " + MovieExcludeFormat
    log(4, funcName + "MovieFormat: " + MovieFormat)
  else:
    log(4, funcName + "Show non-HD movies, so only exclude non-selected formats")
    MovieFormat = MovieExcludeFormat
    log(4, funcName + "MovieFormat: " + MovieFormat)

  log(4, funcName + "Value Returned: " + MovieFormat)
  return MovieFormat

####################################################################################################
def getMovieLanguages():
  funcName = "[getMovieLanguages] "
  # Pretty much a static function for now, with room to grow
  movieLanguages = "" #"&englishonly=1"
  return movieLanguages

####################################################################################################
def getTVLanguages():
  funcName = "[getTVLanguages] "
  # Pretty much a static function for now, with room to grow
  TVLanguages = ""
  return TVLanguages

####################################################################################################
def calcPeriod(days): # days must be a string... legacy, didn't feel like fixing this everywhere
  # NZBMatrix uses days as whole numbers
  period = days
  return period