from configuration import *
from common import *
#from PMS import *
#from PMS.Network import *
#from OpenSSL import SSL
#import socket

DOWNLOAD_MEASURE_TIME = 1 # Number of seconds over which to average download speeds

class nntpManager(AppService):
  #AppService __init__ calls this
  def init(self):
    self.clients = []
    
  def register(self, client):
    funcName = '[nntpManager.register]'
    log(7, funcName, 'Registering a client')
    self.clients.append(client)
  
  def deregister(self, client):
    funcName = '[nntpManager.deregister]'
    log(7, funcName, 'Deregistering a client')
    self.clients.remove(client)
  
  def __str__(self):
    return str(self.clients)
    
  def disconnect_all(self):
    funcName = '[nntpManager.disconnect_all]'
    for client in self.clients:
      try:
        client.disconnect()
      except:
        log(3, funcName, 'Unable to disconnect a client connection')
  
  @property
  def speed(self):
    speed = 0
    for client in self.clients:
      speed += client.speed
    return speed
    
class nntpClient(nntpObj):
  def __init__(self, app):
    funcName = '[nntpClient.init]'
    self.app = app
    self.lock = Thread.Lock()
    if self.nntpSSL:
      log(5, funcName, 'Initializing SSL Socket')
      self.sock = Network.SSLSocket()
      log(5, funcName, 'SSL Socket initialized')
    else:
      log(5, funcName, 'Initializing socket')
      self.sock = Network.Socket()
      log(5, funcName, 'Socket initializied')
    self.app.nntpManager.register(self)
    self.speed = 0
    self.downloaded_bytes = 0
    self.start_download_time = Datetime.Now()
    self.finish_download_time = None
      
  def connect(self):
    funcName='[nntpClient.connect]'
    Thread.AcquireLock(self.lock)
    log(5, funcName, 'Attempting to connect to', self.nntpHost)
    try:
      self.sock.connect((self.nntpHost, int(self.nntpPort)))
      if self.nntpSSL:
        self.sock.do_handshake()

      log(5, funcName, 'Successfully connected')
      # Check that the server is ready
      status_line = self.read_line()
      log(5, funcName, 'Status_line:', status_line)
      if status_line[0:3] != '200':
        raise Exception("Bad status")

      # Try to log in
      self.send_command('authinfo user %s', self.nntpUsername)
      #self.sock.sendall('authinfo user %s\r\n' % self.username)
      status_line = self.read_line()
      if status_line[0:3] != '381':
        raise Exception("Bad username")
    
      self.sock.sendall('authinfo pass %s\r\n' % self.nntpPassword)
      status_line = self.read_line()
      if status_line[0:3] != '281':
        raise Exception("Bad password")
        
      log(5,funcName,"Successfully connected to", self.nntpHost, 'as', self.nntpUsername)
      return True
      
    finally:
      Thread.ReleaseLock(self.lock)
      pass
      	
  def disconnect(self):
    #self.sock.disconnect()
    self.sock.close()
    self.app.nntpManager.deregister(self)
     
  def send_command(self, command, *args):
    self.sock.sendall((command % args) + '\r\n')
    
  def read_line(self):
    data = self.sock.recv(1024)
    lines = data.split('\r\n')
    data = lines.pop()
    return lines[0]
    
  def get_article(self, article_obj):
    funcName = '[nntpClient.nntpClient.get_article]'
    Thread.AcquireLock(self.lock)
    try:
      log(7, funcName, "Downloading article", article_obj.article_id)
      self.send_command('body <%s>', article_obj.article_id)
    
      lines = []
      data = ''
      #self.downloaded_bytes = 0

      while True:
        chunk = self.sock.recv(32768)
        self.finish_download_time = Datetime.Now()
        self.downloaded_bytes = self.downloaded_bytes + len(chunk)
        log(7, funcName, 'elapsed time:', ((self.finish_download_time - self.start_download_time).seconds), 'downloaded bytes:', self.downloaded_bytes)
        if ((self.finish_download_time - self.start_download_time).seconds) >= DOWNLOAD_MEASURE_TIME:
          self.speed = float(self.downloaded_bytes) / float((self.finish_download_time - self.start_download_time).seconds)
          log(7, funcName, 'speed:', self.speed)
          self.start_download_time = Datetime.Now()
          self.downloaded_bytes = 0
        data += chunk
        new_lines = data.split('\r\n')
        data = new_lines.pop()
        lines.extend(new_lines)
      
        if len(lines) > 0 and lines[-1] == '.':
          break
      return lines[1:-1]
    finally:
      Thread.ReleaseLock(self.lock)
      pass