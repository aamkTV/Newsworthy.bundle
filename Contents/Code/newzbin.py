from common import *

SEARCH_URL  = "http://www.newzbin.com/search?fpn=p"
RESULTS_PER_PAGE = 100
NEWZBIN_NAMESPACE = {"report":"http://www.newzbin.com/DTD/2007/feeds/report/"}

CAT_TV = "8"
CAT_MOVIES = "6"

sortFilter = "sort=date&order=desc" #"sort=ps_edit_date&order=desc"

####################################################################################################
def performLogin(nzbService, forceRetry=False):
  funcName = '[newzbin.performLogin]'
  #global SABinfo
  #x = HTTP.Request('http://www.newzbin.com/account/logout/')
  #log(4, funcName, nzbService)
  if nzbService.newzbinUsername != "" and nzbService.newzbinUsername and nzbService.newzbinPassword != "" and nzbService.newzbinPassword:
    values =  {'username': nzbService.newzbinUsername,
               'password': nzbService.newzbinPassword}
    log(8, funcName, 'values being used to login:', values)
    # don't use a cached response if we are retrying the login
    if forceRetry:
      HTTP.ClearCache()

    #Try the login to newzbin
    #x = HTTP.Request("http://www.newzbin.com/", encoding="latin1")
    
    try:
      x = HTTP.Request("http://www.newzbin.com/search?fpn=p", values, encoding="latin1")
      if x and (x.content.count("Log Out") > 0 or x.content.count("days left") > 0):
        log(2,funcName, "Logged into Newzbin")
        return True
      else:
        log(2,funcName, "Login to Newzbin failed.")
        return False
    except Ex.URLError:
      log(4, funcName, Ex.URLError)
      return False
    except:
      log(1, funcName, "Error logging in.")
      return False
  else:
    log(2,funcName, "No username and/or password.")
    return False

      
####################################################################################################
def supportsGenres():
  return True

####################################################################################################
def search(category, queryString, period, page=0):
  funcName = '[newzbin.search]'
  log(5, funcName, 'Constructing URL')

  url = SEARCH_URL + "&searchaction=Search&u_post_results_amt=" + str(RESULTS_PER_PAGE) + "&category=" + category + "&q=" + queryString + "&" + sortFilter + "&u_v3_retention=" + period
  log(5, funcName, "URL:", url)
    
  log(5, funcName, 'Checking page #:',page)
  if page>1:
    url += "&page=" + str(page)

  # We want the rss feed, so it's easy to parse
  url += "&feed=rss"

  log(2, funcName + "URL: " + url)

  allResults = XML.ElementFromURL(url, cacheTime=TVRAGE_CACHE_TIME).xpath('//item')

  allEntries = []
  if len(allResults)>0:
    @parallelize
    def processAllNZBEntries():
      for entry in allResults:
        @task
        def processNZBEntry (entry=entry):

          thisEntry = article()
          thisEntry.title = entry.xpath("title")[0].text
          log(5, funcName, 'Title:', thisEntry.title)
          thisEntry.reportAge = "Report Age: " + entry.xpath("report:postdate",namespaces=NEWZBIN_NAMESPACE)[0].text
          log(5, funcName, 'Report Age:', thisEntry.reportAge)

          if category == CAT_TV:
            #try to get the TVRageURL, if it exists
            try:
              thisEntry.moreInfoURL = entry.xpath("report:moreinfo",namespaces=NEWZBIN_NAMESPACE)[0].text
            except:
              pass
          elif category == CAT_MOVIES:
            #Try to get the imdb id
            try:
              thisEntry.moreInfo = entry.xpath("report:moreinfo",namespaces=NEWZBIN_NAMESPACE)[0].text.split("/")[-2]
            except:
              pass

          log(5, funcName, 'moreInfoURL:', thisEntry.moreInfoURL)
          thisEntry.nzbID = entry.xpath("report:id",namespaces=NEWZBIN_NAMESPACE)[0].text
          thisEntry.newzbinID = entry.xpath("report:id",namespaces=NEWZBIN_NAMESPACE)[0].text
          log(5, funcName, 'newzbinID:', thisEntry.nzbID)

          size = entry.xpath("description")[0].text
          size = size[size.find("Size:")+5:]
          size = size[:size.find(")")]
          thisEntry.size = size
          log(5, funcName, 'size:', size)

          # Get the download size in MB
          if thisEntry.size.count(",")>=1:
            log(5, funcName, "',' found in", thisEntry.size, ' so removing it')
            thisEntry.sizeMB = float(thisEntry.size[:thisEntry.size.find("MB")].replace(",",''))
          else:
            log(5, funcName, "MB found in", thisEntry.size, " so leaving it alone")
            thisEntry.sizeMB = float(thisEntry.size[:thisEntry.size.find("MB")])
          log(5, funcName, 'start size:', thisEntry.size, ', size in mb:', thisEntry.sizeMB)

          allEntries.append(thisEntry)
    
    log(5, funcName, 'Found # Entries:', len(allEntries))
  return allEntries

####################################################################################################
def downloadNZBUrl(nzbID):
  funcName = '[newzbin.downloadNZBUrl]'
  downloadURL = "http://www.newzbin.com/browse/post/%s/nzb" % nzbID
  log(4, funcName, 'NZB Download URL:', downloadURL)
  return downloadURL

####################################################################################################
def getArticleSummary(newzbinID):
  #global articleDict
  postHTML = HTML.ElementFromURL("http://www.newzbin.com/browse/post/" + newzbinID, errors="ignore")
  postSummary = ''
  includeSummaryDetails = True
  warningXML = postHTML.xpath('//div[@class="warning"]')
  for w in warningXML:
    if w.text_content().find("INCOMPLETE FILES DETECTED") > 0:
      postSummary += "*****************************\nWARNING - INCOMPLETE FILES DETECTED\n*****************************\n\n"
      #Log(postSummary)
      includeSummaryDetails = True
    if w.text_content().find("identifying copyrighted content by the MPA.") > 0:
      postSummary += "This Report has been identified as possibly identifying copyrighted content by the MPA and has been removed."
      includeSummaryDetails = False
      break
  if includeSummaryDetails:
    postSummaryTmp =  postHTML.xpath("//div/table//th[contains(.,'Size')]/following-sibling::td[position()=1]")[0].text_content()
    sizeInMB = postSummaryTmp[postSummaryTmp.find("ed:") + 5:postSummaryTmp.find("MB") + 2]
    postSummary +=  "Size:" + sizeInMB #.replace("\t","").replace("\n","").replace("Encoded","\nEncoded").replace("Decoded","\nDecoded")
    postSummary += "\n\n" + postHTML.xpath("//div/table//th[contains(.,'Attributes')]/following-sibling::td[position()=1]")[0].text_content().replace("\t","").replace("\n","").replace("Video","\nVideo").replace("Subtitled Language","\nSubtitles").replace("Language:","\nLanguage:").replace("Audio","\nAudio").replace(": ",":").replace(":",": ").replace("Video ","")
    postSummary += "\n\nNewsgroups: " + postHTML.xpath("//div/table//th[contains(.,'Newsgroups')]/following-sibling::td[position()=1]")[0].text_content().replace("\n","").replace("\t","")
    #articleDict[newzbinID].downloadSizeInMB = float(sizeInMB.replace('MB','').replace(',',''))
  return postSummary

####################################################################################################
def concatSearchList(thelist):
  funcName = "[newzbin.concatSearchList]"

  query=""
  for title in thelist:
  	log(4, funcName + "adding '" + title + "' to the query")
  	if len(query)<=1:
  	  query="(" + title + ")"
  	else:
  	  query+=" or (" + title + ")"
  log(4, funcName + "query: " + query)

  return query

####################################################################################################
def getTVVideoFilters():
  funcName = "[getTVVideoFilters] "
  # The "new-ish" way of filtering video
  TVHDVideoAttributes = "((a:VideoF~720p or a:VideoF~1080i or a:VideoF~1080p) -(a:VideoF~Blu-Ray))"

  videoFilter = ""
  # Check which TV Formats to include
  ShowHD = Prefs['ShowHDTV']
  ShowSD = Prefs['ShowSDTV']
  log(3, funcName + "ShowSDTV: " + str(ShowSD) + " and ShowHDTV: " + str(ShowHD))

  # We are only covering the use cases where someone wants to intentionally filter by HD/SD content.
  # If both are set to true, no need to filter
  # If both are set to off, I'm assuming there's an error and will display all content

  if ((ShowHD) and not (ShowSD)):
    log(4, funcName + "Show only HD Videos")
    videoFilter = TVHDVideoAttributes
    #value += valueSep + TVHDVideoAttributes
  elif ((ShowSD) and not (ShowHD)):
    log(4, funcName + "Show only SD Videos")
    videoFilter = "-" + TVHDVideoAttributes
    #value += valueSep + "-" + TVHDVideoAttributes

  return videoFilter

####################################################################################################
def getMovieVideoFilters():
  funcName = "[getMovieVideoFilters] "
  MovieFormat = ""

  #Check which formats to include
  ShowNonHD = Prefs['ShowNonHDMovies']
  Show720p = Prefs['Show720pMovies']
  Show1080i = Prefs['Show1080iMovies']
  Show1080p = Prefs['Show1080pMovies']
  #ShowBluRay = Prefs['ShowBluRayMovies']

  # Easy use case: All formats to be displayed, no more processing needed
  if (ShowNonHD and Show720p and Show1080i and Show1080p and ShowBluRay):
    log(3, funcName + "All video formats selected, done")
    return MovieFormat

  MovieIncludeFormat = ""
  MovieExcludeFormat = ""
  Attr720p = "a:VideoF~720p"
  Attr1080p = "a:VideoF~1080p"
  Attr1080i = "a:VideoF~1080i"
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

#   if (ShowBluRay):
#     listOfIncludes.append(AttrBluRay)
#   else:
#     listOfExcludes.append(AttrBluRay)

  log(4, funcName + "Selected movie video formats: " + str(listOfIncludes))
  log(4, funcName + "Excluded movie video formats: " + str(listOfExcludes))

  if (len(listOfIncludes) >=1):
    for format in listOfIncludes:
      if(len(MovieIncludeFormat)<=1):
        MovieIncludeFormat += "(" + format
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
    MovieFormat = "(" + MovieIncludeFormat + " " + MovieExcludeFormat + ")"
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
  movieLanguages = "(a:l~English)"
  return movieLanguages

####################################################################################################
def getTVLanguages():
  funcName = "[getTVLanguages] "
  # Pretty much a static function for now, with room to grow
  TVLanguages = "(a:l~English)"
  return TVLanguages

####################################################################################################
def calcPeriod(days): # days must be a string... legacy, didn't feel like fixing this everywhere
  # the number of days * hours in day * minutes in an hour * seconds in an hour
  period = float(days) * 24 * 60 * 60
  return str(period)
