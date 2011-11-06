class NW_Introspector(object):
  def __init__(self, thing):
    self.my_object = thing
  
  @property
  def class_name(self):
    return self.my_object.__class__.__name__
    
class depickler(object):
  import pickle
  def __init__(self, sobject):
    self.sobject = sobject
  def load(self):
    f = open('../' + str(sobject))
    usobject = pickle.load(f)

class MediaItem(object):
  pass

class queue(object):
  pass