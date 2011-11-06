import re
import yenc
import time
import sys

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
  def __init__(self, item, file_obj):
    funcName = '[decoder.Decoder.__init__' + file_obj.name + ']'
    self.parts = dict()
    self.total = None
    self.total_size = 0
    self.decoded_size = 0
    self.filename = None
    self.finished = Thread.Event()
    self.data = ''
    self.parts_expected = file_obj.segment_numbers
    log(9, funcName, 'Expecting:', self.parts_expected)
    self.parts_received = []
    self.skipped_parts = 0
    self.stopped = False
    self.data_parts = Thread.Queue()
    self.queue_lock = Thread.Lock()
    self.threads_running = False
    self.item = item
    #self.start_data_queue()
    
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
  #  if not self.complete:
  #    raise Exception('Parts missing')
      
    data = ''
    Log('Compiling data')
    for x in range(len(self.parts)):
      Log('Compiling data part ' + str(x) + ' of ' + str(len(self.parts)))
      data += self.parts[x+1]
      
    return data
  
  def skip_part(self, part_number):
    self.skipped_parts = self.skipped_parts + 1
    self.parts[part_number] = ''
    self.parts_received.append(part_number)
    
  def add_part_to_data(self):
    fname = '[Decoder.add_part_to_data]'
    log(3, fname, 'Started data queue thread')
    #n=1
    n=self.parts_expected[0]
    while not self.stopped:
    #while ( n < len(self.parts_received)) and (not self.complete):
      log(9, fname, 'Waiting for part', n)
      if self.stopped:
        log(8, fname, 'Stopping add_part_to_data')
        self.finished.set()
        break
      if n in self.parts_received:
        #Log(fname + 'Adding part ' + str(n))
        self.data = self.data + self.parts[n]
        #n += 1
        log(9, fname, 'removing', n, 'from', self.parts_expected)
        try:
          self.parts_expected.remove(n)
        except:
          log(1, funcName, 'Unable to remove part',n, ' Error:', sys.exc_info()[1])
        if len(self.parts_expected) > 0:
          n = self.parts_expected[0]
          if n not in self.parts_received: log(9, fname, self.filename,', Waiting for part:',n)
        #self.parts_received.sort()
        #Log(fname + 'Checking if self.complete: ' + str(self.complete))
        #if self.complete and n > len(self.parts_received):
        if len(self.parts_expected) == 0:
          log(8, fname, 'Done adding parts to data')
          self.finished.set()
          break
      else:
        #log(7, fname, 'Decoder stopped', 'parts expected:', self.parts_expected, 'parts received:', self.parts_received)
        time.sleep(1)
    #else:
      #Log(fname + 'Stopped checking for data.  n=' + str(n) + ', len(self.parts_received)=' + str(len(self.parts_received)) + ', self.complete=' + str(self.complete))
      #Log(fname + 'first test: ' + str(( n < len(self.parts_received))) + ', second test: ' + str(not self.complete))
    #  pass
  
  def add_part(self, data, segment_number):
    self.data_parts.put((data, segment_number))
    if not self.threads_running:
      self.start_data_queue()
  
  def start_data_queue(self):
    funcName = '[Decoder.start_data_queue]'
    if not self.threads_running:
      try:
        Thread.AcquireLock(self.queue_lock)
        if not self.threads_running:
          log(8, funcName, 'Starting data queuing threads')
          Thread.Create(self.add_part_to_data)
          Thread.Create(self.process_part)
          self.threads_running = True
      except:
        err, errno, tb = sys.exc_info()
        log(3, funcName, 'Error:', err, 'errno:', errno, 'tb:', tb)
      finally:
        Thread.ReleaseLock(self.queue_lock)
  
  def process_part(self):
    funcName = '[Decoder.process_part]'
    while True:
      #log(8, funcName, 'Waiting for data')
      if self.stopped:
        log(8, funcName, 'Stopped process_part')
        break
      if self.finished.isSet():
        log(7, funcName, 'This article is complete, ending data processing thread')
        break
	  
      try:
        data, segment_number = self.data_parts.get(False)
      except:
        continue
	    
      if data:
        log(9, funcName, 'Found some data to process, segment number:', segment_number)
        #data = self.data_parts.get(True)
        data = strip(data)
        #print(str(data))
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
            log(1, funcName, 'IndexError', IndexError)
            break

        ## Check tail
        for i in xrange(-1, -11, -1):
          try:
            if data[i].startswith('=yend '):
              yend = ySplit(data[i])
              data = data[:i]
              break
          except IndexError:
            log(1, funcName, 'IndexError', IndexError)
            break

        if not (ybegin and yend):
          log(1, funcName, "Can't handle non-yencoded data")
          log(9, funcName, 'Non-yencoded data:', data)
          self.item.add_failed_article(segment_number) # Article ID is irrelevant
          self.skip_part(segment_number)
          continue
          #raise Exception("Can't handle non-yencoded data:", data)

        if 'name' not in ybegin:
          log(1, funcName, 'Corrupt header detected')
          self.item.add_failed_article(segment_number) # Article ID is irrelevant
          self.skip_part(segment_number)
          continue
          #raise Exception('Corrupt header detected')
	
        filename = ybegin['name']

        decoded_data, crc = yenc.decode_string(''.join(data))[:2]
        partcrc = '%08X' % ((crc ^ -1) & 2**32L - 1)

        if ypart: crcname = 'pcrc32'
        else: crcname = 'crc32'
        
        if crcname not in yend:
          log(1, funcName, 'CRC Name detection failed')
          self.item.add_failed_article(segment_number) # Article ID is irrelevant
          self.skip_part(segment_number)
          continue
          #raise Exception('Corrupt header detected')

        required_partcrc = '0' * (8 - len(yend[crcname])) + yend[crcname].upper()
        
        if partcrc != required_partcrc:
          log(1, funcName, 'CRC check failed:')
          self.item.add_failed_article(segment_number) # Article ID is irrelevant
          self.skip_part(segment_number)
          continue

        # Try to count by part number
        if 'total' in ybegin:
          if self.total == None:
            self.total = int(ybegin['total'])
          else:
            if self.total != int(ybegin['total']):
              self.item.add_failed_article(segment_number) # Article ID is irrelevant
              self.skip_part(segment_number)
              continue
              #raise Exception('Part count mismatch')

        #Log('[Decoder.add_part] self.total: ' + str(self.total))
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

        #Log('[Decoder.add_part] Adding part ' + str(int(yend['part'])) + ' to self.parts')
        try:
          self.parts[int(yend['part'])] = decoded_data
          self.parts_received.append(int(yend['part']))
        except:
          log(1, funcName, 'error in:' + filename)
          self.total=1
          self.parts[1] = decoded_data
          self.parts_received.append(1)
      else:
        log(9, funcName, 'No data found')
        #pass
        #log(9, funcName, 'Found nothing to process, sleeping')
        time.sleep(.25)
    #if self.complete:
    #  self.finished.set()
