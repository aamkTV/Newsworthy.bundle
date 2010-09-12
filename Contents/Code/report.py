class Report(object):
  def __init__(self, el):
    self.title = el.xpath('title')[0].text
    self.url = el.xpath('url')[0].text
    
    #TODO: Attributes
    self.format = None
    self.genres = []
    self.languages = []
    
    self.passworded = False
    self.tags = []
    
    # Get tags
    for tag in el.xpath('tags/tag'):
      title = tag.get('title')
      self.tags.append(title)
    
    # Parse flags
    for flag in el.xpath('flags/flag'):  
      if flag.get('name') == 'passworded':
        self.passworded = (flag.get('bool') == '1')