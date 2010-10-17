#from PMS import *
#from PMS.Objects import *
#from PMS.Shortcuts import *
import re#, httplib
from common import *

name = 'NZBMatrix'
SEARCH_URL = 'http://nzbmatrix.com/nzb-search.php?'
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

#USERNAME = ''
#PASSWORD = ''
LoggedIn = False

####################################################################################################
def performLogin(nzbService, forceRetry=False):
  funcName = '[nzbmatrix.performLogin]'
#  global USERNAME
#  global PASSWORD

  url = 'http://nzbmatrix.com/account-login.php'
  if nzbService.nzbmatrixUsername != "": # and nzbService.nzbmatrixPassword != "":
    USERNAME = nzbService.nzbmatrixUsername
    PASSWORD = nzbService.nzbmatrixPassword
    values = {'username': USERNAME, 'password': PASSWORD}
    log(8,funcName,'nzbmatrix login credentials:',values)

    if forceRetry:
      HTTP.ClearCache()

    ####
    # This used to work, but stopped with Plex/Nine
    # Using HTTP.Request instead
    ####
    #response = XML.ElementFromURL(url=url, isHTML=True, values=values)
    #log(5, funcName, 'http test response:', XML.StringFromElement(response))

    try:
      #x = response.path('//form[@action="account-login.php"]')[0]
      response = HTML.ElementFromURL(url=url, values=values)
      log(5, funcName, 'nzbmatrix login response received')
      x = response.xpath('//a[@href="/account-login.php"]')[0]
      log(4, funcName, 'Found an account-login link')
      log(4, funcName, XML.StringFromElement(x))
    except Ex.URLError:
      log(4,funcName, Ex.URLError)
      return False
    except:
      x = None
      log(4, funcName, 'No account-login link found')

    if x is None:
      log(4, funcName, 'Logged into NZBMatrix')
      return True
    else:
      log(4, funcName, 'Login to NZBMatrix failed.')
      return False
  else:
    log(4, funcName, 'NZBMatrix username/password not specified')
    return False

####################################################################################################
def supportsGenres():
  return False

####################################################################################################
def search(category, queryString, period, page):
  funcName = '[nzbmatrix.search]'
  url = SEARCH_URL + "search=" + queryString + "&cat=" + category + "&maxage=" + period + "&sort=" + sortFilter + "&searchin=name"#&gibberish=" + str(time.time())

  if page>1:
    log(4, funcName, 'page:', page)
    url += "&offset=" + str(((page-1)*RESULTS_PER_PAGE))
  else:
    log(4, funcName, 'page is <1:', page)

  # We want the rss feed, so it's easy to parse
  #url += "&feed=rss"

  log(2, funcName + "URL: " + url)
  #testresp = HTTP.Request(url)
  #log(4, funcName, "http response:",testresp)
  #allResults = XML.ElementFromURL(url, isHTML=True, cacheTime=CACHE_TIME).xpath('//table[@class="nzbtable grid"]//tr[@class!="nzbtable_head"]')
  try:
    allResults = HTML.ElementFromURL(url, cacheTime=CACHE_TIME).xpath('//table[@class="nzbtable grid"]//tr[@class!="nzbtable_head"]')
  except URLError:
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
          if not entryCached or len(thisEntry.reportAge) <= 1: thisEntry.reportAge = "Report Age: " + entry.xpath('td[@class="age nzbtable_data"]')[0].text

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

  funcName = '[nzbmatrix.getTVRageURL]'
  location = ''

  searchURL = "http://www.tvrage.com/search.php?search=" + encodeText(searchValue)
  return searchURL
#  x = HTTP.Request(searchURL)
#  #log(6, funcName, 'headers.content:', x.content)
#  log(6, funcName, 'x.headers:', x.headers)
#  log(6, funcName, 'x.cookies:', HTTP.GetCookiesForURL(".tvrage.com"))
# 
#   try:
#     log(6, funcName, 'Search URL:', searchURL)
#     headers = HTTP.Request(searchURL).headers
#     #log(6, funcName, 'Response:', resp.content)
#     try:
#       log(6, funcName, 'all headers', headers)
#       location = headers['location']
#       log(6, funcName, 'headers[\'location\']', location, ' (length:', len(location) + ")")
#     except:
#       log(6, funcName, 'location not found in response, returning nothing')
#       location = ""
#   except:
#     pass
# 
#  return location
####################################################################################################
# def getTVRageURL(searchValue):
# 
#   funcName = '[nzbmatrix.getTVRageURL]'
#   location = ''
# 
#   searchURL = "/search.php?search=" + encodeText(searchValue)
# 
#   httpConn = httplib.HTTPConnection("www.tvrage.com")
#   try:
#     log(6, funcName, 'Search URL:', searchURL)
#     httpConn.request(method="GET", url=searchURL)
#     httpResp = httpConn.getresponse()
#     log(6, funcName, 'httpResp.status:',httpResp.status)
#     try:
#       location = httpResp.getheader('location')
#       log(6, funcName, 'httpResp.header[\'location\']', location, ' (length:', len(location) + ")")
#     except:
#       log(6, funcName, 'location not found in response, returning nothing')
#       location = ""
#   except:
#     pass
# 
#   return location
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
      if re.match("S[0-9][0-9]E[0-9][0-9]", val):
        log(6, funcName, 'match found on',val)
        cleanName += " " + val
        infoFound=True
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
  #postHTML = XML.ElementFromURL("http://nzbmatrix.com/nzb-details.php?id=" + nzbID)

  #global articleDict
  #postHTML = XML.ElementFromURL("http://www.newzbin.com/browse/post/" + newzbinID, True, errors="ignore")
  #postSummary = ''
  #includeSummaryDetails = True
  #warningXML = postHTML.xpath('//div[@class="warning"]')
  #for w in warningXML:
  #  if w.text_content().find("INCOMPLETE FILES DETECTED") > 0:
  #    postSummary += "*****************************\nWARNING - INCOMPLETE FILES DETECTED\n*****************************\n\n"
  #    #Log(postSummary)
  #    includeSummaryDetails = True
  #  if w.text_content().find("identifying copyrighted content by the MPA.") > 0:
  #    postSummary += "This Report has been identified as possibly identifying copyrighted content by the MPA and has been removed."
  #    includeSummaryDetails = False
  #    break
  #if includeSummaryDetails:
  #  postSummaryTmp =  postHTML.xpath("//div/table//th[contains(.,'Size')]/following-sibling::td[position()=1]")[0].text_content()
  #  sizeInMB = postSummaryTmp[postSummaryTmp.find("ed:") + 5:postSummaryTmp.find("MB") + 2]
  #  postSummary +=  "Size:" + sizeInMB #.replace("\t","").replace("\n","").replace("Encoded","\nEncoded").replace("Decoded","\nDecoded")
  #  postSummary += "\n\n" + postHTML.xpath("//div/table//th[contains(.,'Attributes')]/following-sibling::td[position()=1]")[0].text_content().replace("\t","").replace("\n","").replace("Video","\nVideo").replace("Subtitled Language","\nSubtitles").replace("Language:","\nLanguage:").replace("Audio","\nAudio").replace(": ",":").replace(":",": ").replace("Video ","")
  #  postSummary += "\n\nNewsgroups: " + postHTML.xpath("//div/table//th[contains(.,'Newsgroups')]/following-sibling::td[position()=1]")[0].text_content().replace("\n","").replace("\t","")
  #  articleDict[newzbinID].downloadSizeInMB = float(sizeInMB.replace('MB','').replace(',',''))
  return postSummary

####################################################################################################
def concatSearchList(thelist):
  funcName = "[nzbmatrix.concatSearchList]"

  query=""
  for title in thelist:
    log(4, funcName + "adding '" + title + "' to the query")
    if len(query)<=1:
      query="+((\"" + title.replace("^",'').replace("\"",'') + "\")"
    else:
      query+=" or (\"" + title.replace("^",'').replace("\"",'') + "\")"

  if len(query)>1:
    query+=")"
  log(4, funcName + "query: " + query)

  return query

####################################################################################################
def getTVVideoFilters():
  funcName = "[getTVVideoFilters] "
  TVHDVideoAttributes = "(720p or 1080p or 1080i)"
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
    log(4, funcName + "Show only HD Videos")
    videoFilter = "+" + TVHDVideoAttributes
  elif ((ShowSD) and not (ShowHD)):
    log(4, funcName + "Show only SD Videos")
    videoFilter = "-" + TVHDVideoAttributes

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
  movieLanguages = "&englishonly=1"
  return movieLanguages

####################################################################################################
def getTVLanguages():
  funcName = "[getTVLanguages] "
  # Pretty much a static function for now, with room to grow
  TVLanguages = ""
  return TVLanguages

####################################################################################################
def calcPeriod(days): # days must be a string... legacy, didn't feel like fixing this everywhere
  # the number of days * hours in day * minutes in an hour * seconds in an hour
  period = days
  return period
