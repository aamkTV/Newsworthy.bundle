import updater
WHATS_NEW = 'whats_new_v%s'
class updates(object):
  def __init__(self):
    self.versions = ['0.80', '0.81']
  
  @property
  def show_new(self):
    for version in self.versions:
      if not (WHATS_NEW % version) in Dict:
        return True
    return False
    
  @property
  def whats_new(self):
    whats_new_list = {}
    for version in self.versions:
      #log(8, 'Version:', version)
      if not (WHATS_NEW % version) in Dict:
        #whats_new_list.append(F("WHATS_NEW_V", str(version)))
        update = L("WHATS_NEW_V" + str(version))
        #log(8, 'Update:', update)
        whats_new_list[version] = update
    return whats_new_list
