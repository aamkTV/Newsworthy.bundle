class Unpacker(object):
  def __init__(self, item):
    self.item = item
    self.parts = []
    self.complete = False
    self.stopped = False
    self.waiting = Thread.Event()
    self.play_ready = False
    self.first_part = self.item.nzb.rars[0].name

  def get_contents(self):
    info = Helper.Run('unrar', 'l', Core.storage.join_path(self.item.incoming_path, self.first_part))
    info_lines = info.split('\n')
    info_started = False
    contents = {}
    for line in info_lines:
      if len(line) > 0 and line[0] == '-':
        if info_started:
          break
        else:
          info_started = True
      elif info_started:
        parts = line.split(' ')
        contents[parts[1]] = int(parts[2])
    return contents
    
  def start(self):
    in_path = self.item.incoming_path
    out_path = self.item.completed_path
    first_path = Core.storage.join_path(in_path, self.first_part)
    self.parts.append(self.first_part)

    self.proc = Helper.Process(
      'unrar',
      'e', '-kb', '-vp', '-o+',
      first_path, out_path
    )
    
    Thread.Create(self.monitor)
    
  def add_part(self, part):
    if part not in self.parts:
      self.parts.append(part)
      self.waiting.set()
    
  def monitor(self):
    Log.Debug("Monitor thread started")
    
    data = ''
    while True:
      if self.stopped:
        self.proc.kill()
        break
      elif self.proc.poll() != None:
        break
        
      chunk = self.proc.recv(1)
      if chunk == None:
        self.proc.recv_wait()
        if self.proc.poll() == None:
          continue
        else:
          break
          
      data += chunk
      lines = data.split('\n')
      data = lines.pop()
      for line in lines:
        self.process(line)
        
      if data[:17] == 'Insert disk with ' and data[-20:] == ' [C]ontinue, [Q]uit ':
        next_file = data[17:-20].split('/')[-1]
        data = ''
        
        while True:
          if self.stopped: break
          
          ready = False
          if next_file in self.parts:
            ready = True
          else:
            self.waiting.clear()
          
          if ready:
            break
            
          Log("Waiting for '%s'", next_file)
          self.waiting.wait()
        
        if self.stopped:
          self.proc.send('q\n')
          continue
          
        else:
          self.proc.send('c\n')
    
    final_chunk = self.proc.recv(1024)
    if final_chunk:
      data += final_chunk
    self.process(data)
    
    self.complete = True
    self.item.finished_unpacking()
    
    Log.Debug("Monitor thread ended")
    
  def process(self, line):
    line = line.strip()
    if line[-3:] == '99%' and self.play_ready == False:
      self.play_ready = True
      Log("Contents of '%s' is play-ready", self.first_part)
    
    elif line[:16] == 'Extracting from ':
      part_name = line.split('/')[-1]
      Log("Unpacking '%s'", part_name)
    
    #elif line == 'All OK':
    #  self.complete = True
    #  Log("Finished unpacking archive '%s'", self.first_part)
    #  self.stopped = True
    
    #else:
    #  print 'Processing line: %s' % line
    
  @property
  def running(self):
    return self.proc.poll() == None
