import dateutil
import datetime
import sys
import re

class movie_metadata(object):
  def __init__(self, imdbID):
    self.dataDict = {}
    self.imdbID = imdbID
    self.imdb = imdb(self.imdbID)
    self.tmdb = tmdb(self.imdbID)
  
  @property
  def desc(self):
    if self.imdb.synopsis:
      return self.imdb.synopsis
    elif self.tmdb.synopsis:
      return self.tmdb.synopsis
    else:
      return ''
  
  @property
  def thumb(self):
    if self.imdb.thumb:
      return self.imdb.thumb
    elif self.tmdb.thumb:
      return self.tmdb.thumb
    else:
     return ''
  
  @property
  def fanart(self):
    if self.imdb.fanart:
      return self.imdb.fanart
    elif self.tmdb.fanart:
      return self.tmdb.fanart
    else:
      return ''
  
  @property
  def duration(self):
    if self.imdb.duration:
      return self.imdb.duration
    elif self.tmdb.duration:
      return self.tmdb.duration
    else:
      return ''
  
  @property
  def release_date(self):
    if self.imdb.release_date:
      return self.imdb.release_date
    elif self.tmdb.release_date:
      return self.tmdb.release_date
    else:
      return ''
  
  @property
  def title(self):
    if self.imdb.title:
      return self.imdb.title
    elif self.tmdb.title:
      return self.tmdb.title
    else:
      return ''
      
  @property
  def metadata(self):
    self.dataDict['title'] = str(self.title)
    self.dataDict['desc'] = str(self.desc)
    self.dataDict['thumb'] = str(self.thumb)
    self.dataDict['duration'] = self.duration
    self.dataDict['fanart'] = str(self.fanart)
    self.dataDict['date'] = self.release_date
    return self.dataDict
    
class imdb(object):
  def __init__(self, imdbID):
    if imdbID:
      self.imdbID = imdbID
      self.imdbURL = 'http://www.imdb.com/title/' + self.imdbID + '/'
      try:
        self.imdbResp = HTTP.Request(self.imdbURL, cacheTime=IMDB_CACHE_TIME)
        self.imdbXML = HTML.ElementFromString(self.imdbResp.content)
        self.imdbSynopsisURL = 'http://www.imdb.com/title/' + self.imdbID + '/plotsummary'
        try:
          self.imdbSynopsisResp = HTTP.Request(self.imdbSynopsisURL, cacheTime=IMDB_CACHE_TIME)
          self.imdbSynopsisXML = HTML.ElementFromString(self.imdbSynopsisResp.content)
        except:
          self.imdbSynopsisResp = ''
          self.imdbSynopsisXML = False
      except:
        self.imdbResp = None
        self.imdbXML = None
        self.imdbSynopsisXML = None
  
  @property
  def fanart(self):
    pass
  
  @property
  def title(self):
    funcName = '[imdb.title]'
    try:
      #title = self.imdbXML.xpath('//h1[@class="header"]')[0].text.strip()
      title = self.imdbXML.xpath('//meta[@property="og:title"]')[0].get("content").strip()
    except:
      log(7, funcName, 'Unable to get title:', self.imdbID, 'Error:', sys.exc_info()[1])
      title = ''
    return title
    
  @property
  def duration(self):
    funcName = '[imdb_metadata.duration]'
    try:
      runtime = get_named_value(str(self.imdbResp), "Runtime:</h4>", "</div").strip()
      log(7, funcName, 'runtime:', runtime)
      if runtime > 0:
        duration = runtime[:runtime.rindex("min")].strip()
        duration = int(duration) * 60 * 1000
      else:
        duration = 0
    except:
      log(7, funcName, 'unable to get duration:', self.imdbID, 'error:', sys.exc_info()[1])
      duration = 0
    log(7, funcName, 'duration:', duration)
    return duration

  @property
  def synopsis(self):
    funcName = '[imdb.synopsis]'
    desc = ''
    try:
      if self.imdbSynopsisResp:
        desc = self.imdbSynopsisXML.xpath('//p[@class="plotpar"]')[0].text_content()
      else:
        try:
          desc = self.imdbSynopsisXML.xpath('//div[@class="article"]//p')[0].text_content()
        except:
          desc = self.imdbXML.xpath('//div[@class="article title-overview"]//p')[1].text_content()
    except:
      log(7, funcName, 'Unable to get synopsis:', self.imdbID, ' Error:', sys.exc_info()[1])
      desc = ""
    return desc
  
  @property
  def thumb(self):
    funcName = '[imdb.thumb]'
    try:
      thumb = self.imdbXML.xpath("//td[@id='img_primary']//img")[0].get("src")
    except:
      log(7, funcName, 'Unable to get thumb:', self.imdbID, ' Error:', sys.exc_info()[1])
      thumb = ''
    return thumb
  
  @property
  def release_date(self):
    funcName = '[imdb.release_date]'
    try:
      release = self.imdbXML.xpath('//div[@class="infobar"]//span[@class="nobr"]//a')[0].text
      log(8, funcName, 'release:', release)
      parts = release.split()
      log(8, funcName, 'parts:', parts)
      recombined = parts[0] + " " + parts[1] + " " + parts[2]
      log(8, funcName, 'recombined:', recombined)
      release_date = dateutil.parser.parse(recombined)
      log(7, funcName, 'release_date:', release_date)
      return release_date
    except:
      log(3, funcName, 'Unable to get release date:', self.imdbID, ' Error:', sys.exc_info()[1])
      return ''

  @property
  def rating(self):
    try:
      return self.imdbXML.xpath('//span[@class="rating-rating"]')[0].text
    except:
      return ''

class tmdb(object):
  def __init__(self, imdbID):
    self.dataDict = {}
    self.imdbID = imdbID
    self.tmdbURL = 'http://api.themoviedb.org/2.1/Movie.imdbLookup/en/xml/a3dc111e66105f6387e99393813ae4d5/' + self.imdbID
    try:
      self.tmdbResp = HTTP.Request(self.tmdbURL, cacheTime=IMDB_CACHE_TIME)
      self.tmdbXML = HTML.ElementFromString(self.tmdbResp.content)
    except:
      self.tmdbResp = None
      self.tmdbXML = None
  
  @property
  def title(self):
    funcName = '[tmdb.title]'
    try:
      title = self.tmdbXML.xpath('//name').text
    except:
      log(7, funcName, 'Unable to get name:', self.imdbID, 'Error:', sys.exc_info()[1])
      title = ''
    return title
    
  @property
  def thumb(self):
    funcName = '[tmdb.thumb]'
    try:
      thumb = self.tmdbXML.xpath("images/image[@type='poster' and @size='original']")[0].get('url')
    except:
      log(7, funcName, 'Unable to get thumb:', self.imdbID, ' Error:', sys.exc_info()[1])
      thumb = ''
    return thumb
  
  @property
  def fanart(self):
    funcName = '[tmdb.fanart]'
    try:
      art = self.tmdbXML.xpath("//image[@type='backdrop' and @size='original']")[0].get('url')
      log(7, funcName, 'Fanart:', art)
    except:
      log(7, funcName, 'Unable to get fanart:', self.imdbID, ' Error:', sys.exc_info()[1])
      art = ''
    return art
  
  @property
  def synopsis(self):
    funcName = '[tmdb.synopsis]'
    try:
      desc = self.tmdbXML.xpath("overview")[0].text
    except:
      log(7, funcName, 'Unable to get synopsis:', self.imdbID, ' Error:', sys.exc_info()[1])
      desc = ''
    return desc
  
  @property
  def duration(self):
    funcName = '[tmdb.duration]'
    try:
      runtime = int(self.tmdbXML.xpath("runtime")[0].text) * 60
    except:
      log(7, funcName, 'Unable to get duration:', self.imdbID, ' Error:', sys.exc_info()[1])
      runtime = ''
    return runtime
  
  @property
  def release_date(self):
    funcName = '[tmdb.release_date]'
    try:
      release = self.tmdbXML.xpath('//released')[0].text
      log(7, funcName, 'release:', release)
      release_date = dateutil.parser.parse(release)
      log(7, funcName, 'release_date:', release_date)
      return release_date
    except:
      log(3, funcName, 'Unable to get release date:', self.imdbID, ' Error:', sys.exc_info()[1])
      return ''
    
def get_named_value(data, name, endString):
  """
  Gets the value between two tags.
  Usage:
  For the text: data = <TAG>name:</TAG>text you want<BR>
  'text_you_want' = get_named_value(data, "name:</TAG>", "<BR")
  """
  funcName = '[movie_metadata.get_named_value]'
  try:
    if data:
      Info = data[data.index(name)+(len(name)):data.index(endString, data.index(name))]
      log(8, funcName, 'Name:', name, ' Value:', Info)
      return Info
    else:
      return ""
  except:
    log(3, funcName, 'Error trying to get', name, ' error:', sys.exc_info()[1])
    return ""
