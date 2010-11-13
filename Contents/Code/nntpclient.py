from configuration import *
from common import *
import sys
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
    self.create_sock()
#     if self.nntpSSL:
#       log(5, funcName, 'Initializing SSL Socket')
#       self.sock = Network.SSLSocket()
#       log(5, funcName, 'SSL Socket initialized')
#     else:
#       log(5, funcName, 'Initializing socket')
#       self.sock = Network.Socket()
#       log(5, funcName, 'Socket initializied')
    self.app.nntpManager.register(self)
#     self.speed = 0
#     self.downloaded_bytes = 0
#     self.start_download_time = Datetime.Now()
#     self.finish_download_time = None
    self.retries = 0
    self.max_retries = 2
  
  def create_sock(self):
    funcName = '[nntpClient.create_sock]'
    if self.nntpSSL:
      log(5, funcName, 'Initializing SSL Socket')
      self.sock = Network.SSLSocket()
      log(5, funcName, 'SSL Socket initialized')
    else:
      log(5, funcName, 'Initializing socket')
      self.sock = Network.Socket()
      log(5, funcName, 'Socket initializied')
      self.speed = 0
    self.downloaded_bytes = 0
    self.start_download_time = Datetime.Now()
    self.finish_download_time = None

  def connect(self):
    funcName='[nntpClient.connect]'
    Thread.AcquireLock(self.lock)
    log(5, funcName, 'Attempting to connect to', self.nntpHost)
    try:
      self.sock.settimeout(1.0)
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
  
  def article_exists(self, article_id):
    funcName = '[nntpClient.article_exists]'
    log(7, funcName, 'checking if article exists:', article_id)
    self.send_command('body <%s>', article_id)
    data = self.sock.recv(256)
    if data[:3] != '430':
      return True
    else:
      return False
  
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
  
  def flush(self):
    funcName = '[nntpClient.nntpClient.flush]'
    data = ''
    while True:
      self.flush_times = self.flush_times + 1
      log(8, funcName, 'flushing:', self.flush_times)
      data = self.sock.recv(32768)
      lines = data.split('\r\n')
      log(8, funcName, 'last lines:', lines[-5:-1])
      log(8, funcName, 'len(lines):', len(lines), 'lines[-1]:', lines[-1])
      if len(lines) > 0 and ('.' in lines[-2:-1] ):
        break
    log(8, funcName, 'end!')
      
  def get_article(self, article_obj):
    funcName = '[nntpClient.nntpClient.get_article]'
    retry = False
    Thread.AcquireLock(self.lock)
    try:
      #if not self.article_exists(article_obj.article_id): raise ('Article Not Found', 430)
      log(8, funcName, "Downloading article", article_obj.article_id)
      self.send_command('body <%s>', article_obj.article_id)
    
      lines = []
      data = ''
      #self.downloaded_bytes = 0

      try:
        while True:
          chunk = self.sock.recv(32768)
          if chunk[:3] == '430':
            raise nntpException('Article Not Found', 430)
          
          #test of the system
          # find this in common.py now.  test_article_failure = [32, 33]
          if article_obj.segment_number in test_article_failure:
            log(1, funcName, 'Simulating error on segment', test_article_failure)
            self.flush_times = 0
            self.flush()
            log(7, funcName, 'Done flushing!')
            raise nntpException('Article Not Found', 430)
              
          self.finish_download_time = Datetime.Now()
          self.downloaded_bytes = self.downloaded_bytes + len(chunk)
          #log(7, funcName, 'elapsed time:', ((self.finish_download_time - self.start_download_time).seconds), 'downloaded bytes:', self.downloaded_bytes)
          if ((self.finish_download_time - self.start_download_time).seconds) >= DOWNLOAD_MEASURE_TIME:
            self.speed = float(self.downloaded_bytes) / float((self.finish_download_time - self.start_download_time).seconds)
            log(8, funcName, 'speed:', self.speed)
            self.start_download_time = Datetime.Now()
            self.downloaded_bytes = 0
          data += chunk
          new_lines = data.split('\r\n')
          data = new_lines.pop()
          lines.extend(new_lines)
          
          #if len(lines) > 0 and (lines[-1] == '.' or lines[-2] == '.'):
          if len(lines) > 0 and lines[-1] == '.':
            break
        return lines[1:-1]
      except nntpException:
        type, exception, traceback = sys.exc_info()
        if exception.id == 430:
          raise
        else:
          log(1, funcName, 'nntp error, id:', id, ', mesg:', mesg, ', tb:', tb)
      except:
        error, msg, tb = sys.exc_info()
        #log(7, lines)
        #raise
        #if errnum==54 or errstr=="Connection reset by peer":
        if self.retries < self.max_retries:
          log(2, funcName, 'error:', error, ', msg:', msg, 'tb:', tb)
          log(2, funcName, 'Connection reset by peer, retrying')
          self.retries = self.retries + 1
          retry = True
          Thread.ReleaseLock(self.lock)
          self.create_sock()
          self.connect()
          self.get_article(article_obj)
        else:
          log(1, funcName, 'Connection reset by peer, retried', self.max_retries, 'times, no luck')
          raise
        #else:
        #  raise
    finally:
      if not retry: Thread.ReleaseLock(self.lock)
      self.retries = 0
      pass