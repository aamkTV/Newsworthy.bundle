import re

# Convenience function for getting an xpath with the Newzbin namespace
ns_xpath = lambda el, xp: el.xpath(xp, namespaces={'nzb':'http://www.newzbin.com/DTD/2003/nzb'})

# A list of the extensions we care about
extensions = ['rar', 'par2', re.compile(r'r\d\d')]

class NZArticle(object):
  def __init__(self, article_id, size):
    self.size = size
    self.article_id = article_id
    self.complete = False

class NZFile(object):
  def __init__(self, el):
    
    self.name = None
    self.ext = None
    self.articles = []
    
    
    """ Try to find the file's extension """
    
    subject = el.get('subject')
    
    part = subject[subject.find('"')+1:subject.rfind('"')]
      
    # Check if there's something that appears to be a file extension
    index = part.rfind('.')
    if index == -1: return
    
    possible_ext = part[index+1:]
    
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
      #print "No extension for %s" % subject
      return
    
    self.name = part
    
      
    """ Store the file segments in a list """

    for segment_el in ns_xpath(el, 'nzb:segments/nzb:segment'):
      article = NZArticle(segment_el.text, int(segment_el.get('bytes')))
      self.articles.append(article)
      
  def __repr__(self):
    return 'NZFile(%s)' % self.name
    
  @property
  def percent_done(self):
    total = self.total_bytes
    done = self.downloaded_bytes        
    return int((float(done) / float(total)) * 100)
    
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
        done = done + article_obj.size
    return done
    

class NZB(object):
  def __init__(self, el):
    self.rars = []
    self.pars = []
    
    rars = []
    rnns = []
    
    for file_el in ns_xpath(el, 'nzb:file'):
      file_obj = NZFile(file_el)

      # Check that we matched a file extension
      if not file_obj.ext: continue
      
      # See what type of file we have
      if file_obj.ext == 'rar':
        rars.append(file_obj)
      elif file_obj.ext == 'par2':
        self.pars.append(file_obj)
      else:
        rnns.append(file_obj)
        
    # Sort the rars and add them to the list
    self.rars.extend(Util.ListSortedByAttr(rars, 'name'))
    self.rars.extend(Util.ListSortedByAttr(rnns, 'name'))