import re
import sys
from common import *

name = 'NZBIndex.nl'
SEARCH_URL = 'http://www.nzbindex.nl/rss/'

sortFilter = "&sort=agedesc"
defaultQuery = ''#"&dq=nfo"
spamFilter = "&hideSpam=1"
nfoFilter = "&hasnfo=1"

max_query_items = 9

CACHE_TIME = 30 # seconds
CAT_TV = 'TV'
CAT_MOVIES = 'Movies'
RESULTS_PER_PAGE = 50

MOVIE_BROWSING = False
TV_BROWSING = True
TV_SEARCH = True
MOVIE_SEARCH = False

#LoggedIn = False

####################################################################################################
def performLogin(nzbService, forceRetry=False):
  funcName = '[' + name + '.performLogin]'

  url = SEARCH_URL + "?q=Please+dont+find+anything+that+matches+me+this+crazy+and_improbably+long+name&max=1"
  try:
    response = HTTP.Request(url)
    log(9, funcName, 'Response:', response)
    log(9, funcName, 'Response Headers:', response.headers)
    if response.headers['content-type'].find('text/xml') != -1:
      log(5, funcName, 'Successfully \'logged in\' to NZBIndex.nl')
      return True
    else:
      log(1, funcName, 'Error ''logging in'' to NZBIndex.nl:', response)      
  except Ex.URLError:
      log(4,funcName, Ex.URLError)
      return False
  except:
      log(1, funcName, 'Error starting NZBIndex.nl:', sys.exc_info()[1])
      return False

####################################################################################################
def supportsGenres():
  return False

####################################################################################################
def search(category, query_list, period, page):
  funcName = '[' + name + '.search]'
  
  #query_values = concatSearchList(query_list)
  query_values = query_list
    
  allEntries = []
  new_list = []
  while len(query_values) > 0:
    while len(new_list) < max_query_items:
      if len(query_values) > 0:
        new_list.append(query_values.pop())
        log(7, funcName, 'new_list:', new_list)
      else:
        log(7, funcName, 'Out of query_list items')
        break
    log(4, funcName, 'Complete query list:', new_list)
    query_new_list = concatSearchList(new_list)
    allEntries.extend(getResults(category=category, query_values=query_new_list, period=calcPeriod(period), page=page))
    new_list = []
  return allEntries
    
####################################################################################################
def getResults(category, query_values, period, page):
  funcName = '[' + name + '.getResults]'

  # Add any video format filters
  if category == CAT_TV:
    VideoFilters = getTVVideoFilters()
    LanguageFilters = getTVLanguages()
  elif category == CAT_MOVIES:
    VideoFilters = getMovieVideoFilters()
    LanguageFilters = getMovieLanguages()
  if len(VideoFilters)>0: query_values += " " + VideoFilters
  if len(LanguageFilters)>0: query_values += " " + LanguageFilters
  
  url = SEARCH_URL + "?q=" + String.Quote(query_values) + "&age=" + period + sortFilter + defaultQuery + spamFilter + nfoFilter + "&max=" + str(RESULTS_PER_PAGE)
  
  # Pages for NZBIndex start at 0.  The default for Newzworthy is 1.  Decrement by 1 to avoid chaos.
  page = page - 1
  if page>0:
    log(4, funcName, 'page:', page)
    url += "&page=" + str(page)
  else:
    log(4, funcName, 'page is <1:', page)

  log(2, funcName + "URL: " + url)
  #testresp = HTTP.Request(url)
  #log(4, funcName, "http response:",testresp)
  #allResults = XML.ElementFromURL(url, isHTML=True, cacheTime=CACHE_TIME).xpath('//table[@class="nzbtable grid"]//tr[@class!="nzbtable_head"]')
  try:
    log(5, funcName, 'Getting results for', url)
    try:
      allResults = XML.ElementFromURL(url, cacheTime=CACHE_TIME).xpath('//item')
    except:
      log(1, funcName, 'Error getting results:', sys.exc_info()[1])
      raise
    log(1, funcName, 'Got Results:', allResults)
  except URLError:
    raise
  except:
    log(1, funcName, 'Error searching:', sys.exc_info()[1])
    raise

  allEntries = []
  log(5,funcName,'Getting Dict:',nzbItemsDict)
  nzbItems = Dict[nzbItemsDict]
  log(5,funcName, 'Got Dict:',nzbItemsDict,nzbItems)
  if len(allResults)>0:
    @parallelize
    def processAllNZBEntries():

      for entry in allResults:

        @task
        def processNZBEntry (entry=entry):
          entryCached = False
          thisEntry = article()
          log(9, funcName, 'string:', XML.StringFromElement(entry))
          title = entry.xpath('title')[0].text
          link = entry.xpath('link')[0].text
          guid = entry.xpath('guid')[0].text
          thisEntry.nzbID = Hash.CRC32(title + link + guid)
          log(1, funcName, 'CRC32 Calculated ID:', thisEntry.nzbID)

          thisEntry.newzbinID = thisEntry.nzbID
          if thisEntry.nzbID in nzbItems:
            log(5, funcName, 'key found!')
            thisEntry = nzbItems[thisEntry.nzbID]
            entryCached = True

          CData = entry.xpath('description')[0].text
          CDataHTML = HTML.ElementFromString(CData)
          if CData.find('Password Protected') == -1:
          
            if not entryCached or len(thisEntry.title) <= 1: thisEntry.title = entry.xpath('title')[0].text
            if not entryCached or len(thisEntry.size) <= 1: thisEntry.size = CDataHTML.xpath('//b')[0].text
            thisEntry.reportAge = "Report Age: " + entry.xpath('pubDate')[0].text
            

            if category == CAT_TV:
              # Why bother if it's already cached?
              if not entryCached and len(thisEntry.moreInfoURL) <=1:
                cleanName = removeExtraWords(thisEntry.title)
                #This will try to find the TVRageURL
                if len(cleanName) > 1:
                  log(5, funcName, 'finding TVRageURL for', cleanName)
                  thisEntry.title = cleanName
                  thisEntry.moreInfoURL = getTVRageURL(cleanName) #TVRageURL
              else:
                log(4, funcName, 'Adding TV Show', thisEntry.title, 'from the cache')

            elif category == CAT_MOVIES:
              if not entryCached or len(thisEntry.moreInfo) <= 1:
                if not removeExtraWords(thisEntry.title):
                  thisEntry.moreInfo = getIMDBid(thisEntry.nzbID)
                else:
                  log(5, funcName, 'I think', thisEntry.title, 'is a TV show, not adding it to the movie list')
              else:
                log(4, funcName, 'Adding Movie', thisEntry.title, 'from the cache')

            log(5, funcName, 'moreInfoURL:',thisEntry.moreInfoURL, 'moreInfo:', thisEntry.moreInfo)

            # Get the download size in MB
            if not entryCached or thisEntry.sizeMB<=1:
              if thisEntry.size.count("GB")>=1:
                log(6, funcName, "GB found in", thisEntry.size, ' so multiplying by 1000')
                thisEntry.sizeMB = float(thisEntry.size[:thisEntry.size.find("GB")])*1000
              elif thisEntry.size.count("MB")>=1:
                log(6, funcName, "MB found in", thisEntry.size, " so leaving it alone")
                thisEntry.sizeMB = float(thisEntry.size[:thisEntry.size.find("MB")])
              log(6, funcName, 'start size:', thisEntry.size, ', size in mb:', thisEntry.sizeMB)
            
            try:
              thisEntry.downloadURL = entry.xpath('enclosure')[0].get('url')
              log(8, funcName, 'Download URL from enclosure:', thisEntry.downloadURL)
            except:
              log(3, funcName, 'Could not get enclosure url, trying permalink')
              try:
                thisEntry.downloadURL = entry.xpath('guid')[0].text
                log(8, funcName, 'Download URL from GUID:', thisEntry.downloadURL)
              except:
                log(1, funcName, 'Could not get guid as download url, no download url')
                thisEntry.downloadURL = ''
                
          else: #Password protected
            thisEntry.title = "Password Protected"
          allEntries.append(thisEntry)

  return allEntries

####################################################################################################
def getIMDBid(nzbID):
  funcName = '[' + name + '.getIMDBLink]'
  imdbID = ''

  detailsPageURL = "http://nzbmatrix.com/nzb-details.php?id=" + nzbID
  try:
    imdbID = HTML.ElementFromURL(url=detailsPageURL, cacheTime=CACHE_TIME).xpath('//ul[@id="nzbtabs"]//a[@target="_blank"]')[0]
    imdbID = HTML.StringFromElement(imdbID)
    tokens = imdbID.split("/")
    for val in tokens:
      if re.match("tt[0-9][0-9][0-9]", val):
        imdbID = str(val)
  except:
    pass
  log(4,funcName, 'imdbID:', imdbID)
  return imdbID
####################################################################################################
def getTVRageURL(searchValue):

  funcName = '[' + name + '.getTVRageURL]'
  location = ''

  searchURL = "http://www.tvrage.com/search.php?search=" + encodeText(searchValue)
  return searchURL

####################################################################################################
def removeExtraWords(value):
  funcName = '[' + name + '.removeExtraWords]'

  cleanName = ""
  infoFound = False
  old_value = value
  try:
    value = old_value[old_value.index('"')+1:]
  except:
    pass
  log(5, funcName, 'Trying to remove pre-roll junk.  Starting with:', old_value, 'Ending with:', value)
  char_dict = {}
  char_dict['.'] = value.count(".")
  char_dict['_'] = value.count("_")
  char_dict[' '] = value.count(" ")
  char_dict['-'] = value.count("-")
  try:
    #sepChar = sepChar[sorted(char_dict, key=char_dict.get, reverse=True)[0]]
    sepChar = sorted(char_dict, key=char_dict.get, reverse=True)[0]
  except:
    log(1, funcName, 'Error finding separator character:', value, sys.exc_info()[1])
    sepChar=" "

  #if numSpaces > numUnderScores and numSpaces > numPeriods: sepChar=" "
  #if numPeriods > numUnderScores and numPeriods > numSpaces: sepChar="."
  #if numUnderScores > numPeriods and numUnderScores > numSpaces: sepChar="_"
  tokens=value.split(sepChar)
  log(5, funcName, 'String:', value, 'sepChar:', sepChar, 'char_dict:', char_dict)
  for val in tokens:
    if not infoFound:
      log(6, funcName, 'checking the token "' + val + '"')
      if re.match("(?i)S?\d\d?([(?i)E|x])?\d\d?", val):
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
  funcName = '[' + name + '.downloadNZBUrl]'
  #downloadURL = "http://nzbmatrix.com/nzb-download.php?id=" + nzbID + "&nozip=1"
  #log(4, funcName, 'NZB Download URL:', downloadURL)
  nzbItems = Dict[nzbItemsDict]
  entry = nzbItems[nzbID]
  downloadURL = entry.downloadURL
  return downloadURL

####################################################################################################
def getArticleSummary(nzbID):
  funcName = '[' + name + '.getArticleSummary]'
  postSummary = ''
  return postSummary

####################################################################################################
def concatSearchList(thelist):
  funcName = '[' + name + ".concatSearchList]"

  query=""
  for title in thelist:
    log(4, funcName + "adding '" + title + "' to the query")
    if len(query)<=1:
      query="\"" + title.replace("^",'').replace("\"",'') + "\""
    else:
      query+=" | \"" + title.replace("^",'').replace("\"",'') + "\""

  #if len(query)>1:
  #  query+=")"
  log(4, funcName + "query: " + query)

  return query

####################################################################################################
def getTVVideoFilters():
  funcName = '[' + name + ".getTVVideoFilters] "
  TVHDVideoAttributes = "720p | 1080p | 1080i"
  videoFilter = ""
  # Check which TV Formats to include
  log(4, funcName, 'Getting TVVideoPreferences')
  ShowHD = (Prefs['ShowHDTV'])
  ShowSD = (Prefs['ShowSDTV'])
  log(8, funcName + "ShowSDTV: " + str(ShowSD) + " and ShowHDTV: " + str(ShowHD))
  # We are only covering the use cases where someone wants to intentionally filter by HD/SD content.
  # If both are set to true, no need to filter
  # If both are set to off, I'm assuming there's an error and will display all content

  if ((ShowHD) and not (ShowSD)):
    log(4, funcName + "Show only HD Videos")
    videoFilter = TVHDVideoAttributes
  elif ((ShowSD) and not (ShowHD)):
    log(4, funcName + "Show only SD Videos")
    videoFilter = "-" + TVHDVideoAttributes

  return videoFilter

####################################################################################################
def getMovieVideoFilters():
  funcName = '[' + name + ".getMovieVideoFilters]"
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
      #log(8, funcName, 'Adding Include Video Format:', format)
      if len(MovieIncludeFormat)<=1:
        MovieIncludeFormat += " " + format
      else:
        MovieIncludeFormat += " | " + format
#       if(len(MovieIncludeFormat)<=1):
#         MovieIncludeFormat += "+(" + format
#       else:
#         MovieIncludeFormat += " or " + format
#    MovieIncludeFormat+= ")"

  log(3, funcName + "MovieIncludeFormat string: " + MovieIncludeFormat)

  if (len(listOfExcludes) >=1):
    for format in listOfExcludes:
      if(len(MovieExcludeFormat)<=1):
        MovieExcludeFormat += "-" + format
      else:
        MovieExcludeFormat += " -" + format
#    MovieExcludeFormat += ")"

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
  funcName = '[' + name + ".getMovieLanguages] "
  # Pretty much a static function for now, with room to grow
  #movieLanguages = "&englishonly=1"
  movieLanguages = ""
  return movieLanguages

####################################################################################################
def getTVLanguages():
  funcName = '[' + name + ".getTVLanguages] "
  # Pretty much a static function for now, with room to grow
  TVLanguages = ""
  return TVLanguages

####################################################################################################
def calcPeriod(days): # days must be a string... legacy, didn't feel like fixing this everywhere
  # the number of days * hours in day * minutes in an hour * seconds in an hour
  period = days
  return period
