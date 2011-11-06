class UnpackerManager(AppService):
  def init(self):
    self.unpackers = []
  
  def get_unpacker(self, id):
    funcName = '[UnpackerManager.get_unpacker]'
    up = False
    for unpacker in self.unpackers:
      if unpacker.item.id == id:
        up = unpacker
        #log(7, funcName, 'Got unpacker:', up, ' with item.id', up.item.id)
        break
      else:
        log(7, funcName, 'Looking for:', id, 'compared against:', unpacker.item.id)
    return up
    
  def new_unpacker(self, id):
    item = self.app.queue.getItem(id)
    up = Unpacker(item, self.app)
    self.unpackers.append(up)
    return up
    
  def end_unpacker(self, id):
    funcName = '[UnpackerManager.end_unpacker]'
    up = self.get_unpacker(id)
    if up:
      log(5, funcName, 'Stopping unpacker:', id)
      up.stopped = True
    try:
      self.unpackers.remove(up)
      return True
    except:
      return False
    
class Unpacker(object):
  def __init__(self, item, app):
    funcName = "[Unpacker.__init__]"
    log(6, funcName, 'Unpacker started')
    self.app = app
    self.item = item
    self.parts = []
    self.complete = False
    self.stopped = False
    self.waiting = Thread.Event()
    self.play_ready = False
    self.first_part = self.item.nzb.rars[0].name

  def get_contents(self):
    funcName = '[Unpacker.get_contents]'
    OS = Platform.OS
#    log(3, funcName, 'OS: ', OS)
    if OS in ("MacOSX", "Linux"):
      log(3, funcName, 'Starting', OS, 'unrar')
      info = Helper.Run('unrar', 'l', Core.storage.join_path(self.item.incoming_path, self.first_part))
      log(3, funcName, 'info:', info)
#    else:
#      return
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
        partIsNum = False
        partOne = ""
        size = 0
        for x in range(len(parts)):
          log(6, funcName, 'Part being evaluated: "' + str(parts[x]) + '"')
          if parts[x].isdigit() and len(parts[x]) > 4: #4 digits could be a year e.g. Gremlins 1984
            partIsNum = True
            size = int(parts[x])
            break # by now we got our name and filesize
          else:
            if partOne != "":
              #log(7, funcName, "x=" + str(x), "len(parts):", len(parts))
              #if x != len(parts):
              partOne = partOne + " " + parts[x]
            else:
              partOne = parts[x]
          log(6, funcName, 'partOne right now: "' + str(partOne) + '"')
        log(8, funcName, 'removing extra spaces on the right: "' + str(partOne) + '"')
        partOne = partOne.rstrip(" ")
        contents[partOne] = size
        log(6, funcName, 'contents being returned:"' + str(contents) + '"')
        #contents[parts[1]] = int(parts[2])
    return contents
    
  def start(self):
    funcName = '[start] '
    in_path = self.item.incoming_path
    Log.Debug(funcName + 'Incoming path: ' + str(in_path))
    out_path = self.item.completed_path
    Log.Debug(funcName + 'Completed path')
    first_path = Core.storage.join_path(in_path, self.first_part)
    Log.Debug(funcName + 'First path: ' + str(first_path))
    self.parts.append(self.first_part)
    Log.Debug(funcName + 'Parts: ' + str(self.parts))

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
    funcName = '[unpacker.monitor]'
    Log.Debug("Monitor thread started")
    
    data = ''
    allData = ''
    while True:
      if self.stopped:
        self.proc.kill()
        log(3, funcName, 'Unpacker killed')
        break
      elif self.proc.poll() != None:
        try:
          data += self.proc.recv(1)
        except:
          pass
        log(3, funcName, 'Unpacker process has ended (1) with returncode ', self.proc.returncode, 'and allData:', allData)
        break
        
      chunk = self.proc.recv(1)
      if chunk == None:
        self.proc.recv_wait()
        if self.proc.poll() == None:
          continue
        else:
          log(3, funcName, 'Unpacker process has ended (2), allData:', allData)
          break
      
      allData += chunk
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
            
          log(5, funcName, "Waiting for ", next_file)
          self.waiting.wait()
        
        if self.stopped:
          log(3, funcName, 'Quitting unpacker')
          self.proc.send('q\n')
          continue
          
        else:
          log(5, funcName, 'Sending continue command')
          self.proc.send('c\n')
      #else:
      #  try:
      #    log(5, funcName, 'Still waiting for', next_file)
      #  except:
      #    log(5, funcName, 'Waiting for a file')
      #    pass
          
    final_chunk = self.proc.recv(1024)
    if final_chunk:
      data += final_chunk
    self.process(data)
    
    self.complete = True
    self.item = self.app.queue.getItem(self.item.id)
    self.item.finished_unpacking()
    
    Log.Debug("Monitor thread ended")
    
  def process(self, line):
    funcName = '[unpacker.process]'
    line = line.strip()
    unpackedPercent = line[-3:-1]
    Log.Debug('% unpacked: ' + str(unpackedPercent))
#    if line[-3:] == '99%' and self.play_ready == False:
    try:
      int(unpackedPercent)
      unpackedPercentIsNumber = True
    except:
      unpackedPercentIsNumber = False
    
    if unpackedPercentIsNumber and unpackedPercent >= 98 and not self.play_ready:
      self.play_ready = True
      Log.Debug("Contents of '%s' is play-ready", self.first_part)
    
    elif line[:16] == 'Extracting from ':
      part_name = line.split('/')[-1]
      Log.Debug("Unpacking '%s'", part_name)
    
    #elif line == 'All OK':
    #  self.complete = True
    #  Log("Finished unpacking archive '%s'", self.first_part)
    #  self.stopped = True
    
    else:
      log(7, funcName, 'Line:' + line)
    
  @property
  def running(self):
    return self.proc.poll() == None
