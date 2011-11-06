import re

# Convenience function for getting an xpath with the Newzbin namespace
ns_xpath = lambda el, xp: el.xpath(xp, namespaces={'nzb':'http://www.newzbin.com/DTD/2003/nzb'})

# A list of the extensions we care about
extensions = ['rar', 'par2', 'nfo', 'sfv', re.compile(r'r\d\d')]

class NZArticle(object):
  def __init__(self, article_id, size, segment_number):
    self.size = size
    self.article_id = article_id
    self.segment_number = segment_number
    self.complete = False
    self.failed = False
  def __repr__(self):
    ret = 'Segment Number: ' + str(self.segment_number)
    ret += ', article id: ' + str(self.article_id)
    return ret
  def __str__(self):
    ret = 'Segment Number: ' + str(self.segment_number)
    ret += ', article id: ' + str(self.article_id)
    return ret    

class NZFile(object):
  def __init__(self, el):
    funcName = '[nzb.NZFile.__init__]'
    self.name = None
    self.ext = None
    self.articles = []
    self.size = 0
    self.segments = []
    
    self.loading = True
    
    """ Try to find the file's extension """
    
    subject = el.get('subject')
    log(9, funcName, 'subject:', subject, 'el:', el)
    
    part = subject[subject.find('"')+1:subject.rfind('"')]
    log(9, funcName, 'part:', part)
    #part = self.determineFileName(subject)
    
    # Check if there's something that appears to be a file extension
    index = part.rfind('.')
    if index == -1:
      log(3, funcName, 'index==-1')
      return
    
    possible_ext = part[index+1:index+5].lower().strip()
    
    for ext_candidate in extensions:
      # If the candidate is a string, check for an exact match
      if isinstance(ext_candidate, basestring):
        if ext_candidate == possible_ext:
          self.ext = possible_ext
          break
        
      # Otherwise, assume it's a regex, and try to match
      elif ext_candidate.match(possible_ext):
        self.ext = possible_ext
        break
    
    # If there's no matched extension, don't bother parsing the rest of the element - we don't care about it
    if not self.ext:
      log(5, funcName, 'No extension for:', subject)#print "No extension for %s" % subject
      return
    
    self.name = part
      
    """ Store the file segments in a list """

    for segment_el in ns_xpath(el, 'nzb:segments/nzb:segment'):
      article = NZArticle(segment_el.text, int(segment_el.get('bytes')), int(segment_el.get('number')))
      if not article.segment_number in self.segment_numbers:
        self.articles.append(article)
        self.size = self.size + article.size
    
    log(9, funcName, 'file:', self.name, 'segment numbers:', self.segment_numbers)
    self.loading = False
    
  def remove_articles(self):
    self.articles = []
    return True
    
  def __repr__(self):
    return 'NZFile(%s)' % self.name
    
  @property
  def percent_done(self):
    total = self.total_bytes
    done = self.downloaded_bytes        
    return ((float(done) / float(total)) * 100)
    
  @property
  def total_bytes(self):
    total = 0
    for article_obj in self.articles:
      total = total + article_obj.size
    return total
    
  @property
  def downloaded_bytes(self):
    done = 0
    for article_obj in self.articles:
      if article_obj.complete:
        done += article_obj.size
    return done
  
  @property
  def segment_numbers(self):
    #if self.loading: self.segments = []
    #if len(self.segments) <= 0:
    if True:
      self.segments = []
      for art in self.articles:
        self.segments.append(art.segment_number)
      self.segments.sort()
    return self.segments
    
  @property
  def recovery_blocks(self):
    blocks = 0
    if self.ext == 'par2':
      blocks_found = self.name[self.name.rfind("+")+1:self.name.rfind(".")]
      if blocks_found.isdigit(): blocks = int(blocks_found)
    return blocks

class NZB(object):
  def __init__(self, el):
    funcName = "[nzbf.NZB.__init__]"
    self.rars = []
    self.pars = []
    self.total_bytes = 0
    self.total_recovery_blocks = 0
    
    rars = []
    rnns = []
    
    for file_el in ns_xpath(el, 'nzb:file'):
      file_obj = NZFile(file_el)
      log(9, funcName, 'File found:', file_obj.name, 'parts:', len(file_obj.articles))
      log(10, funcName, 'File found:', file_obj.name, 'parts:', file_obj.articles)

      # Check that we matched a file extension
      if not file_obj.ext: continue
      
      # See what type of file we have
      if re.search("[\w._-]?sample[\w._-]?", file_obj.name.lower()) or re.search("[\w._-]?subs[\w._-]?", file_obj.name.lower()):
        #skipping sample files
        log(6, funcName, 'skipping sample file:', file_obj.name)
        continue
      #Skip files with extensions that are irrelevant
      #if file_obj.ext not in extensions: continue
      
      if file_obj.ext == 'rar':
        rars.append(file_obj)
      elif file_obj.ext == 'par2':
        self.total_recovery_blocks = self.total_recovery_blocks + file_obj.recovery_blocks
        self.pars.append(file_obj)
        #print ("Recovery blocks available: " + str(self.total_recovery_blocks))
      elif file_obj.ext == 'nfo' or file_obj.ext == 'sfv':
        self.pars.append(file_obj)
      else:
        rnns.append(file_obj)
        
      # Keep track of the total file size
      self.total_bytes = self.total_bytes + file_obj.total_bytes
        
    # Sort the rars and add them to the list
    self.rars.extend(Util.ListSortedByAttr(rars, 'name'))
    self.rars.extend(Util.ListSortedByAttr(rnns, 'name'))
    #self.rars.extend(Util.ListSortedByAttr(self.pars, 'name'))
  
  def downloaded_bytes(self):
    funcName = '[nzbf.NZB.downloaded_bytes]'
    downloaded = 0
    for file in self.rars:
      downloaded += file.downloaded_bytes
    return downloaded
    
  