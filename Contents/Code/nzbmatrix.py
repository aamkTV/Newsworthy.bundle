import re
import sys
from common import *

name = 'NZBMatrix'
SEARCH_URL = 'http://nzbmatrix.com/nzb-search.php?'
LOGIN_URL = 'http://nzbmatrix.com/account-login.php'
COOKIE_URL = 'http://nzbmatrix.com'
ACCOUNT_URL = 'http://nzbmatrix.com/account.php'
API_URL = ACCOUNT_URL + '?action=api'
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

max_query_length = 50

MOVIE_BROWSING = True
TV_BROWSING = True
TV_SEARCH = True
MOVIE_SEARCH = True

LoggedIn = False
cookie = None


####################################################################################################
def getNZBInfo():
  funcName = '[%s.getNZBInfo]' % name
  nzbService = NZBService()
  log(6, funcName, 'Getting nzbMatrix Username')
  nzbService.nzbmatrixUsername = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixUsername')
  log(6, funcName, 'nzbMatrix Username:', nzbServiceInfo.nzbmatrixUsername)
  nzbService.nzbmatrixPassword = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixPassword')
  log(8, funcName, 'nzbMatrix Password:', nzbServiceInfo.nzbmatrixPassword)
  nzbService.nzbmatrixAPIKey = getConfigValue(theDict=nzbConfigDict, key='nzbMatrixAPIKey')
  return nzbService
  
####################################################################################################
def performLogin(nzbService, forceRetry=False):
  funcName = '[nzbmatrix.performLogin]'
  
  if nzbService.nzbmatrixUsername != "": # and nzbService.nzbmatrixPassword != "":
    USERNAME = nzbService.nzbmatrixUsername
    PASSWORD = nzbService.nzbmatrixPassword
    values = {'username': USERNAME, 'password': PASSWORD}
    log(8,funcName,'nzbmatrix login credentials:', values)

    if forceRetry:
      log(3, funcName, 'Forcing the login retry, clearing the cache')
      HTTP.ClearCache()

    try:
      #HTTP.RandomizeUserAgent()
      rsp = HTTP.Request(url=LOGIN_URL, values=values, immediate=True, timeout=HTTP_TIMEOUT)
      log(5, funcName, 'nzbmatrix login response received')
      headers = rsp.headers
      log(9, funcName, 'response headers:', headers)
      log(9, funcName, 'cookies:', HTTP.CookiesForURL(COOKIE_URL))
      try:
        global cookie
        cookie = HTTP.CookiesForURL('http://nzbmatrix.com')
      except:
        log(4, funcName, 'No cookies found, not logged in')
        return False
      
      cookie_tokens = cookie.split(";")
      log(4, funcName, 'cookie tokens:', cookie_tokens)
      tokens = {}
      for tok in cookie_tokens:
        name = tok.split("=")[0].strip()
        value = tok.split("=")[1].strip()
        tokens[name] = value
      
      log (4, funcName, 'cookie name value pairs:', tokens)
      if tokens['uid'] != 'null':
        return True
      else:
        return False
      
    except Ex.URLError, e:
      log(4,funcName, "URL Error:", e.reason)
      return False
    except:
      log(1, funcName, 'Error logging in:', sys.exc_info()[1])
  else:
    log(4, funcName, 'NZBMatrix username/password not specified')
    return False

####################################################################################################
def supportsGenres():
  return False

####################################################################################################
def search(category, query_list, period, page):
  funcName = '[' + name + '.search]'
  
  #query_values = concatSearchList(query_list)
  query_values = query_list

  # Add any video format filters
  if category == CAT_TV:
    VideoFilters = getTVVideoFilters()
    LanguageFilters = getTVLanguages()
  elif category == CAT_MOVIES:
    VideoFilters = getMovieVideoFilters()
    LanguageFilters = getMovieLanguages()
#  if len(VideoFilters)>0: query_values += " " + VideoFilters
#  if len(LanguageFilters)>0: query_values += LanguageFilters
  
  max_query_length_with_filters = max_query_length - len(VideoFilters) - len(LanguageFilters) - 1
  allEntries = []
  new_list = []
  while len(query_values) > 0:
    current_query_length = len(concatSearchList(new_list))
    while current_query_length < max_query_length_with_filters:
      if len(query_values) > 0:
        if current_query_length + len(query_values[0]) < max_query_length_with_filters:
          new_list.append(query_values.pop())
          log(7, funcName, 'new_list:', new_list)
          current_query_length = len(concatSearchList(new_list))
        else:
          log(7, funcName, 'Maximum query length reached')
          break
      else:
        log(7, funcName, 'Out of query_list items')
        break
    log(4, funcName, 'Complete query list:', new_list)
    query_new_list = concatSearchList(new_list) + " " + VideoFilters
    allEntries.extend(getResults(category=category, query_values=query_new_list, period=calcPeriod(period), page=page))
    new_list = []
  return allEntries
    
####################################################################################################
def getResults(category, query_values, period, page):
  funcName = '[' + name + '.getResults]'
  
#  if len(query_list)>0 and query_list[0]<>'':
#    query_values = concatSearchList(query_list)
#  else:
#    query_values = ''
  

  if page>1:
    log(4, funcName, 'page:', page)
    offset = "&offset=" + str(((page-1)*RESULTS_PER_PAGE))
  else:
    log(4, funcName, 'page is <1:', page)
    offset = ''
    
  # Add any video format filters
  if category == CAT_TV:
#     VideoFilters = getTVVideoFilters()
    LanguageFilters = getTVLanguages()
  elif category == CAT_MOVIES:
#     VideoFilters = getMovieVideoFilters()
    LanguageFilters = getMovieLanguages()
#   if len(VideoFilters)>0: query_values += " " + VideoFilters
  if len(LanguageFilters)>0: query_values += LanguageFilters

  url = SEARCH_URL + "search=" + String.Quote(query_values,usePlus=False) + "&cat=" + category + "&maxage=" + period + "&" + sortFilter + "&searchin=name" + offset#&gibberish=" + str(time.time())

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
    allResults = HTML.ElementFromString(response.content).xpath('//table[@class="nzbtable_table grid"]//tr[@class!="nzbtable_head"]')
    #allResults = HTML.ElementFromURL(url, cacheTime=0).xpath('//table[@class="nzbtable grid"]//tr[@class!="nzbtable_head"]')
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
  if len(allResults)>0:
    @parallelize
    def processAllNZBEntries():

      for entry in allResults:

        @task
        def processNZBEntry (entry=entry):
          entryCached = False
          thisEntry = article()
          add_to_allEntries = True
          thisEntry.nzbID = entry.xpath('td[2]/a[2]/@href')[0]

          #At some point nzbmatrix started adding some more info on the URL.  This isolates just the ID part of the URL
          if thisEntry.nzbID.count("&") > 0:
            log(6, funcName, 'Found an & in the URL, trying to isolate the ID')
            startOfID = thisEntry.nzbID.find("id=")

            thisEntry.nzbID = thisEntry.nzbID[(startOfID+3):thisEntry.nzbID.find("&")]
            log(6, funcName, 'id string:',thisEntry.nzbID, 'start of id position:',startOfID,'and id:',thisEntry.nzbID)
          else:
            log(6, funcName, 'No & found, assuming ID is the only thing in the nzb URL')
            thisEntry.nzbID = thisEntry.nzbID[thisEntry.nzbID.find("=")+1:]

          thisEntry.newzbinID = thisEntry.nzbID
          if thisEntry.nzbID in nzbItems:
            log(5, funcName, 'key found!')
            thisEntry = nzbItems[thisEntry.nzbID]
            entryCached = True

          if not entryCached or len(thisEntry.title) <= 1: thisEntry.title = entry.xpath('td[3]//span["ctitle*"]//b')[0].text
          if not entryCached or len(thisEntry.size) <= 1: thisEntry.size = entry.xpath('td[4]')[0].text
          thisEntry.reportAge = "Report Age: " + entry.xpath('td[@class="age nzbtable_data"]')[0].text
          
          if period > 0:
            #log(7, funcName, 'ReportAge:', entry.xpath('td[@class="age nzbtable_data"]')[0].text)
            #add_to_allEntries = False
            age_num, age_period = entry.xpath('td[@class="age nzbtable_data"]')[0].text.split(" ")
            if age_period == "d":
              #age_num = int(age_num)
              if int(age_num) > int(period):
                log(4, funcName, 'Skipping entry:', thisEntry.title, 'due to old age:', thisEntry.reportAge)
                add_to_allEntries = False
            
          if add_to_allEntries:
            if category == CAT_TV:
              # Why bother if it's already cached?
              if not entryCached and len(thisEntry.moreInfoURL) <=1:
                cleanName = removeExtraWords(thisEntry.title)
                #This will try to find the TVRageURL
                if len(cleanName) > 1:
                  log(5, funcName, 'finding TVRageURL for', cleanName)
                  thisEntry.moreInfoURL = getTVRageURL(cleanName) #TVRageURL
              else:
                log(4, funcName, 'Adding TV Show', thisEntry.title, 'from the cache')

            elif category == CAT_MOVIES:
              if not entryCached or len(thisEntry.moreInfo) <= 1:
                thisEntry.moreInfo = getIMDBid(thisEntry.nzbID)
              else:
                log(4, funcName, 'Adding Movie', thisEntry.title, 'from the cache')

            log(5, funcName, 'moreInfoURL:',thisEntry.moreInfoURL, 'moreInfo:', thisEntry.moreInfo)
          
            #Now start retrieving the metadata
            cache_time = 0
            if category == CAT_MOVIES: cache_time = IMDB_CACHE_TIME
            if category == CAT_TV: cache_time = TVRAGE_CACHE_TIME
            #HTTP.PreCache(thisEntry.moreInfoURL, cacheTime=cache_time)

            # Get the download size in MB
            if not entryCached or thisEntry.sizeMB<=1:
              if thisEntry.size.count("GB")>=1:
                log(6, funcName, "GB found in", thisEntry.size, ' so multiplying by 1000')
                thisEntry.sizeMB = float(thisEntry.size[:thisEntry.size.find("GB")])*1000
              elif thisEntry.size.count("MB")>=1:
                log(6, funcName, "MB found in", thisEntry.size, " so leaving it alone")
                thisEntry.sizeMB = float(thisEntry.size[:thisEntry.size.find("MB")])
              log(6, funcName, 'start size:', thisEntry.size, ', size in mb:', thisEntry.sizeMB)
            allEntries.append(thisEntry)

  return allEntries

####################################################################################################
def getIMDBid(nzbID):
  funcName = "[nzbmatrix.getIMDBLink]"
  imdbID = ''

  detailsPageURL = "http://nzbmatrix.com/nzb-details.php?id=" + nzbID
  try:
    imdbID = HTML.ElementFromURL(url=detailsPageURL, cacheTime=CACHE_TIME, timeout=HTTP_TIMEOUT).xpath('//ul[@id="nzbtabs"]//a[@target="_blank"]')[0]
    imdbID = HTML.StringFromElement(imdbID)
    log(9, funcName, 'Looking for imdbID in string:', imdbID)
    tokens = imdbID.split("/")
    for val in tokens:
      #log(9, funcName, 'Analyzing this token for imdbID:', val)
      if re.match("tt[0-9]{4,8}", val):
        imdbID = str(val)
        break
  except:
    pass
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
def getAPIKey():
  funcName = "[" + name + ".getAPIKey]"
  
  try:
    nzbInfo = getNZBInfo()
    LoggedIn = performLogin(nzbInfo)
    if LoggedIn:
      try:
        rsp = HTTP.Request(API_URL)
        log(9, funcName, 'Response:', rsp.content)
        rspXML = HTML.ElementFromString(rsp.content)
        log(9, funcName, 'fieldset:', rspXML.xpath('//fieldset')[0].text_content())
        api_key = rspXML.xpath('//fieldset//font')[0].text
        log(9, funcName, 'api_key:', api_key)
        return api_key
      except:
        log(1, funcName, 'Error getting api key:', sys.exc_info()[1])
        return False
    else:
      log(3, funcName, 'Not logged in')
      return False
  except:
    log(1, funcName, 'Error before trying to get api key:', sys.exc_info()[1])
    return False
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
