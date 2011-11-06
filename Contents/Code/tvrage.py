import sys
import dateutil
import re
class tv_metadata(object):
  def __init__(self, title, **kwargs):
    funcName = '[tv_metadata.__init__]'
    self.title = title
    if "tvRageURL" in kwargs:
      self.tvRageURL = kwargs["tvRageURL"]
      
class tv_com(object):
  def __init__(self, title=None, id=None, **kwargs):
    self.dataDict = {}
    self.title = clean_title(title)
    self.id = id
    self.searchURL = "http://www.tv.com/search.php?type=11&stype=episode&tag=search%3B&qs=" + self.title
  
  def clean_title(self, title):
    funcName = '[tv_com.clean_title]'
    new_title = title.replace("-", "").replace("\"", "")
    log(5, funcName, 'title:', title, ' new title:', new_title)
    return new_title
    
class TV_RAGE_METADATA(object):
  
  def __init__(self, tvRageURL):
    funcName = '[TV_RAGE_METADATA.__init__]'
    self.api_key = '0sjI1FBecAhO6sLEA9ap'
    self.dataDict = {}
    self.pageDataXML = None
    self.url = tvRageURL
    self.check_url()
    self.get_data()
    self.votes = ''
    self.duration = 60
    self.episode_info_logged = False
    self.episode_info_cache = None
    log(7, funcName, 'Showing metadata')
    #log(7, funcName, 'Data:', self.metadata)
    if not self.valid_data:
      if self.url.lower().find("episodes") > -1:
        parts = self.url.split("/")
        lastPart = ''
        i = 1
        while lastPart == '':
          lastPart = parts[len(parts)-i]
          log(5, funcName, 'url:', self.url, ' lastPart:', lastPart)
          i+=1
        if not lastPart.isdigit() and not lastPart.lower() == "episodes":
          parts.remove(lastPart)
          new_url = "/".join(parts)
          log(3, funcName, 'Trying a different URL:', new_url)
          test = TV_RAGE_METADATA(new_url)
          if test.valid_data:
            self.url = new_url
            self.get_data()
  
  def check_url(self):
    funcName = '[tvrage.check_url]'
    ep_text = "episodes"
    search_text = "search.php?search="
    api_show_search_url = 'http://services.tvrage.com/myfeeds/search.php?key=' + self.api_key + '&show='
    api_episode_search_url = 'http://services.tvrage.com/myfeeds/episodeinfo.php?key=' + self.api_key + '&sid=%s&ep='
    log(8, funcName, 'starting url:', self.url)
    if self.url.count(ep_text) == 1 and self.url.count(search_text) == 0:
      pass
    else:
      try:
        log(3, funcName, 'URL did not pass the test:', self.url)
        if self.url.count(search_text) > 0:
          search_string = self.url[self.url.rindex(search_text)+len(search_text):]
          log(3, funcName, 'String from URL:', search_string)
          # Look for patterns like S01E02, S1E2, 1x2, or 01x02
          re_group = re.search("S?\d\d?[E|x]\d\d?", search_string)
          if re_group:
            episode_identifier = re_group.group()
            search_string = search_string[:re_group.start()] + search_string[re_group.end():]
            #search_string = re.sub("S\d\dE\d\d", search_string)
            log(3, funcName, 'Cleaned up string:', search_string)
          show_search_url = api_show_search_url + search_string
          log(3, funcName, 'Show search query:', show_search_url)
          showSearchXML = XML.ElementFromURL(show_search_url)
          try:
            show_id = showSearchXML.xpath('//showid')[0].text
            log(3, funcName, 'Search string:', search_string, ' show_id:', show_id)
          except:
            log(2, funcName, 'Unable to get show_id.  Error:', sys.exc_info()[1])
            return
            
        #Assume we have a show_id
        #First, the episode identifier needs to look like 1x1 or 01x01
        episode_identifier = episode_identifier.lower().replace("s", "").replace("e","x")
        episode_search_url = api_episode_search_url % show_id + episode_identifier
        log(3, funcName, 'Episode search query:', episode_search_url)
        try:
          episodeSearchXML = XML.ElementFromURL(episode_search_url)
          link = episodeSearchXML.xpath('//url')[0].text
          if link: self.url = link
        except:
          log(1, funcName, 'Error getting episode data:', sys.exc_info()[1])
      except:
        log(1, funcName, 'Error trying to get good data:', sys.exc_info()[1])
  
  def get_data(self):
    funcName = '[tvrage.get_data]'
    try:
      log(7, funcName, 'Looking for URL:', self.url)
      tvRageResp = HTTP.Request(self.url, cacheTime=TVRAGE_CACHE_TIME)
      #log(7, funcName, 'tvRageURL.count("episodes"):',self.url.count("episodes"), 'tvRageURL.count("search.php?search="):', self.url.count("search.php?search="))
      self.pageDataXML = HTML.ElementFromString(str(tvRageResp.content))
      #log(7, funcName, 'XML loaded')
      #log(9, funcName, XML.StringFromElement(self.pageDataXML))
    except:
      self.pageDataXML = None
    
  @property
  def valid_data(self):
    funcName = '[tvrage.valid_data]'
    invalid_data = 0
    invalid_data_threshold = 3
    #log(7, funcName, 'Checking series name')
    #if not self.series_name: invalid_data+=1
    #log(7, funcName, 'Checking summary')
    if not self.summary: invalid_data+=1
    #log(7, funcName, 'Checking title')
    if not self.title: invalid_data+=1
    if not self.season: invalid_data+=1
    if not self.episode: invalid_data+=1
    if not self.date: invalid_data+=1
    if invalid_data >= invalid_data_threshold:
      log(1, funcName, 'Invalid data attributes:', invalid_data, ' url:', self.url)
      return False
    return True
    
  @property
  def metadata(self):
    self.dataDict["seriesName"] = str(self.series_name)
    self.dataDict["summary"] = str(self.summary)
    self.dataDict["title"] = str(self.title)
    self.dataDict["season"] = str(self.season)
    self.dataDict["episode"] = str(self.episode)
    self.dataDict["airDate"] = str(self.air_date)
    #self.dataDict["episode_info"] = self.episode_info
    self.dataDict["votes"] = self.votes
    self.dataDict["thumb"] = str(self.thumb)
    self.dataDict["duration"] = self.duration
    self.dataDict["date"] = self.date
    self.dataDict['episode_title'] = str(self.episode_title)
    return self.dataDict
  
  @property
  def episode_title(self):
    funcName = '[tvrage.episode_title]'
    try:
      epTitle = ''
      try:
        desc = self.pageDataXML.xpath("//meta[@name='description']")[0].get("content").split("@")[0].strip().replace(" Episode","")
        desc = desc.split("|")[0].strip()
        epTitle = desc.split("-")[1].strip().replace("\"", "")
        if not epTitle: raise Exception("Episode Title not available in the meta description")
      except:
        desc = self.pageDataXML.xpath("//div[@class='grid_7_5 box margin_top_bottom left']//font[@size='3']")[0].text
        epTitle = title_area.split(":")[1].strip()
      return epTitle
    except:
      log(4, funcName, 'Error getting episode title:', sys.exc_info()[1])
      return ''
      
  @property
  def title(self):
    funcName = '[tvrage.title]'
    try:
      title = self.series_name + ": " + self.episode_title + " (S" + self.season + "E" + self.episode + " - " + self.date.strftime('%x') + ")"
      log(8, funcName, 'Title:', title)
      return title
    except:
      log(4, funcName, 'Error getting title:', sys.exc_info()[1])
      return ""

  @property
  def series_name(self):
    funcName = '[tvrage.series_name]'
    try:
      name = ''
      try:
        name = self.pageDataXML.xpath('//h1[@class="content_title hover_blue"]//a')[0].text
        if not name: raise Exception("Series Name not in H1")
      except:
        title_area = self.pageDataXML.xpath("//div[@class='grid_7_5 box margin_top_bottom left']//font[@size='3']")[0].text
        name = title_area.split(":")[0].strip()
      log(8, funcName, 'Series Name:', name)
      return name
    except:
      log(4, funcName, 'Error trying to get series name. URL:', self.url, 'Error:', sys.exc_info()[1])
      return ""
  
  @property
  def episode_info(self):
    funcName = '[tvrage.episode_info]'
    #if self.episode_info_cache: return self.episode_info_cache
    EpInfo = None
    div_class = "grid_7_5 box margin_top_bottom left"
    div_class_search_string = '//div[@class="' + div_class + '"]'
    try:
      blocks = self.pageDataXML.xpath(div_class_search_string)
      the_text = "Episode Info"
      if not self.episode_info_logged: log(9, funcName, 'Found', len(blocks), 'instances of the div class:', div_class)
      for block in blocks:
        try:
          #log(9, funcName, 'h1s past div:', HTML.StringFromElement(block.xpath('//div[@class="' + div_class + '"]')))
          if not self.episode_info_logged: log(9, funcName, 'Examining block:', HTML.StringFromElement(block))
          if not self.episode_info_logged: log(9, funcName, 'h1[0]:', block.xpath('h1')[0].text_content())
          block_h1_text = block.xpath('h1')[0].text_content()
          if block_h1_text == the_text:
            if not self.episode_info_logged: log(9, funcName, 'Found', the_text)
            EpInfo = block.xpath('table//tr//td')[0]
            break
          else:
            if not self.episode_info_logged: log(9, funcName, block_h1_text, 'does not equal', the_text)
        except:
          if not self.episode_info_logged: log(9, funcName, 'Error examining block:', sys.exc_info()[1])
      if not EpInfo:
        if not self.episode_info_logged: log(9, funcName, 'No matching block found')
        raise Exception("No Episode Info found")
      EpInfo = HTML.StringFromElement(EpInfo)
      if not self.episode_info_logged: log(9, funcName, 'Episode Info:', EpInfo)
      #self.p_episode_info = EpInfo
      if not self.episode_info_logged: self.episode_info_logged = True
      self.episode_info_cache = EpInfo
      return EpInfo
    except:
      log(4, funcName, 'Unable to get episode info')
      raise
      return False
  
  @property
  def air_date(self):
    funcName = '[tvrage.air_date]'
    try:
      if self.episode_info:
        #airdate = self.episode_info[self.episode_info.index("Airdate: </b>")+(len("Airdate: </b>")):self.episode_info.index("<br", self.episode_info.index("Airdate: </b>"))]
        airdate = self.get_named_value("Airdate: </b>", "<br")
        log(8, funcName, 'Airdate:', airdate)
        return airdate
      else:
        return ""
    except:
      log(4, funcName, 'Error trying to get airdate')
      return ""
  
  @property
  def date(self):
    funcName = '[tvrage.date]'
    try:
      if self.air_date:
        airdate = dateutil.parser.parse(self.air_date)
        log(8, funcName, 'Date:', airdate)
        return airdate
      else:
        return ""
    except:
      log(3, funcName, "Error getting parsed airdate:", self.title)
      return ""
        
  @property
  def season(self):
    funcName = '[tvrage.season]'
    try:
      if self.episode_info:
        seasonAndEp = self.get_named_value("Episode number: </b>", "<br")
        season = seasonAndEp.split("x")[0]
        if len(season) < 2: season = "0" + season
        log(8, funcName, 'Season:', season)
        return season
      else:
        return ""
    except:
      log(4, funcName, 'Error trying to get season')
      return ""

  @property
  def episode(self):
    funcName = '[tvrage.episode]'
    try:
      if self.episode_info:
        seasonAndEp = self.get_named_value("Episode number: </b>", "<br")
        episode = seasonAndEp.split("x")[1]
        if len(episode) < 2: episode = "0" + episode
        log(8, funcName, 'Episode:', episode)
        return episode
      else:
        return ""
    except:
      log(4, funcName, 'Error trying to get episode')
      return ""
  
  @property
  def summary(self):
    funcName = '[tvrage.summary]'
    summary_type = ""
    try:
      summary_type = "Show Synopsis"
      info = self.pageDataXML.xpath('//div[@class="show_synopsis"]')[0].text_content()
      log(8, funcName, 'Show Synopsis summary:', info)
      if len(info.strip()) < 1:
        # The show synopsis div didn't have the show summary.  Try another place.
        summary_type = "span"
        info = self.pageDataXML.xpath('//span[@class="left margin_top_bottom"]//div')[2].text_content()
        log(8, funcName, 'span summary:', info)
      #log(8, funcName, 'Summary:', info)
      if info == None or info.lstrip().lower().startswith("click here to"): info = "No show summary available"
      info = info.replace('.Source:', ".\n\nSource:")
      try:
        if info.rindex("var addthis") > 0:
          info = info[:info.rindex("var addthis")]
      except:
        pass
      return info.lstrip().rstrip() + "\n\nSummary Provided By TVRage.com"
    except:
      err, msg, tb = sys.exc_info()
      log(4, funcName, 'Error getting', summary_type, 'summary:', err, msg, tb)
      #return (str(err) + str(msg) + str(tb))
      return ''
  
  @property
  def thumb(self):
    funcName = '[tvrage.thumb]'
    try:
      thumb = self.pageDataXML.xpath('//div[@class="grid_7_5 box margin_top_bottom left"]//div//img')[0].get("src")
      return thumb
    except:
      log(4, funcName, 'Error getting thumb:', sys.exc_info()[0], sys.exc_info()[1])
      return ""
      
  def get_named_value(self, name, endString):
    """
    Gets the value between two tags.
    Usage:
    For the text: <TAG>name:</TAG>text you want<BR>
    'text_you_want' = get_named_value("name:</TAG>", "<BR")
    """
    funcName = '[tvrage.get_named_value]'
    try:
      if self.episode_info:
        EpInfo = self.episode_info
        Info = EpInfo[EpInfo.index(name)+(len(name)):EpInfo.index(endString, EpInfo.index(name))]
        log(8, funcName, 'Name:', name, ' Value:', Info)
        return Info
      else:
        return ""
    except:
      log(4, funcName, 'Error trying to get', name)
      return ""
    
