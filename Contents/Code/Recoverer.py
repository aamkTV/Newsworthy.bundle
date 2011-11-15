import re, sys

class Recoverer(object):
  def __init__(self, app, item):
    self.app = app
    self.item = item
    self.proc = None
    self.recoverable = False
    self.repair_percent = 0
    self.recovery_complete = False
    self.stopped = False
    self.unpacker = None
    
    #Thread.Create(self.recover_process)
  
  def start(self):
    funcName = '[Recoverer.start]'
    for par in self.item.nzb.pars:
      if par.ext.lower() == "par2" and par.name.lower().find("vol") > 0:
        #log(3, funcName, 'recovering', Core.storage.join_path(self.item.incoming_path, self.item.nzb.pars[0].name))
        log(3, funcName, 'recovering', Core.storage.join_path(self.item.incoming_path, par.name))
        self.proc = Helper.Process('par2', 'r', Core.storage.join_path(self.item.incoming_path, par.name))
        break
    Thread.Create(self.recover_process)
    
  def recover_process(self):
    funcName = '[Recoverer.recover_process]'
    #self.proc = Helper.Process(
    #  'par2SL', 'r', self.item.incoming_path, self.item.nzb.pars[0]
    #  )
    
    data = ''
    while True:
      if self.stopped:
        self.proc.kill()
        break
      if self.proc.poll() != None:
        break
      
      chunk = self.proc.recv(4096)
      if chunk == None:
        self.proc.recv_wait()
        if self.proc.poll() == None:
          continue
        else:
          break
      
      data += chunk
      lines = data.split('\n')
      for line in lines:
        if len(line): log(8, funcName, 'processing this line:', line)
        if not self.recoverable:
          if line[:22] == 'Repair is not possible':
            log(3, funcName, 'Repair is not possible, stopping')
            self.recoverable = False
            self.recovery_complete = True
            self.proc.kill()
            break
          elif line[:18] == 'Repair is possible':
            log(3, funcName, 'Repair is possible, continuing')
            self.recoverable = True
            #data = ''
          elif line[:46] == 'All files are correct, repair is not required.':
            log(3, funcName, 'Repair is not needed, ending successfully')
            self.recoverable = True
            self.recovery_complete = True
            self.repair_percent = 100
            self.proc.kill()
        
        if self.recoverable and not self.recovery_complete:
          if line[:11] == 'Repairing: ':
            self.repair_percent = int(line[line.rfind(':')+2:line.rfind('.')])
            #self.repair_percent = int(line[-6:-3])
            log(6, funcName, 'Repair progress:', self.repair_percent)
            #data = ''
          if line[:15] == 'Repair complete':
            log(3, funcName, 'Repair complete')
            self.recovery_complete = True
            self.proc.kill()
            break
      data = ''
