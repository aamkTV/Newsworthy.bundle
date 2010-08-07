import re
import yenc
YSPLIT_RE = re.compile(r'([a-zA-Z0-9]+)=')

def ySplit(line, splits = None):
  fields = {}

  if splits:
    parts = YSPLIT_RE.split(line, splits)[1:]
  else:
    parts = YSPLIT_RE.split(line)[1:]

  if len(parts) % 2:
    return fields

  for i in range(0, len(parts), 2):
    key, value = parts[i], parts[i+1]
    fields[key] = value.strip()

  return fields
  
def strip(data):
  while data and not data[0]:
    data.pop(0)

  while data and not data[-1]:
    data.pop()

  for i in xrange(len(data)):
    if data[i][:2] == '..':
      data[i] = data[i][1:]
  return data
  
class Decoder(object):
  def __init__(self):
    self.parts = dict()
    self.total = None
    self.total_size = 0
    self.decoded_size = 0
    self.filename = None
    self.finished = Thread.Event()
    
  @property
  def complete(self):
    return ((self.total != None) and (len(self.parts) == self.total)) or (self.total_size > 0 and self.total_size == self.decoded_size)
    
  @property
  def percent_done(self):
    return int((float(self.decoded_size) / float(self.total_size)) * 100)
    
  def wait(self):
    self.finished.wait()
    
  @property
  def decoded_data(self):
    if not self.complete:
      raise Exception('Parts missing')
      
    data = ''
    for x in range(len(self.parts)):
      data += self.parts[x+1]
      
    return data
    
  def add_part(self, data):
    data = strip(data)
    
    """yCheck from SAB decoder.py"""
    ybegin = None
    ypart = None
    yend = None

    ## Check head
    for i in xrange(10):
      try:
        if data[i].startswith('=ybegin '):
          splits = 3
          if data[i].find(' part=') > 0:
            splits += 1
          if data[i].find(' total=') > 0:
            splits += 1

          ybegin = ySplit(data[i], splits)

          if data[i+1].startswith('=ypart '):
            ypart = ySplit(data[i+1])
            data = data[i+2:]
            break
          else:
            data = data[i+1:]
            break
      except IndexError:
        break

    ## Check tail
    for i in xrange(-1, -11, -1):
      try:
        if data[i].startswith('=yend '):
          yend = ySplit(data[i])
          data = data[:i]
          break
      except IndexError:
        break

    if not (ybegin and yend):
      raise Exception("Can't handle non-yencoded data")

    if 'name' not in ybegin:
      raise Exception('Corrupt header detected')

    filename = ybegin['name']
    
    decoded_data, crc = yenc.decode_string(''.join(data))[:2]
    partcrc = '%08X' % ((crc ^ -1) & 2**32L - 1)
    
    if ypart: crcname = 'pcrc32'
    else: crcname = 'crc32'

    if crcname not in yend: raise Exception('Corrupt header detected')

    required_partcrc = '0' * (8 - len(yend[crcname])) + yend[crcname].upper()
    
    if partcrc != required_partcrc: raise Exception('CRC check failed')

    # Try to count by part number
    if 'total' in ybegin:
      if self.total == None:
        self.total = int(ybegin['total'])
      else:
        if self.total != int(ybegin['total']):
          raise Exception('Part count mismatch')
          
    # If this post doesn't include the total number of parts, count by size instead
    if self.total_size == 0:
      self.total_size = int(ybegin['size'])
    elif self.total_size != int(ybegin['size']):
      raise Exception('Total size mismatch')
    self.decoded_size = self.decoded_size + int(yend['size'])
      
    if self.filename == None:
      self.filename = ybegin['name']
    else:
      if self.filename != ybegin['name']:
        raise Exception('Filename mismatch')
    
    self.parts[int(yend['part'])] = decoded_data
    
    if self.complete:
      self.finished.set()