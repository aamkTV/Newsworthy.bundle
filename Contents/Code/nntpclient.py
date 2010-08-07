from configuration import *
from common import *
#from PMS import *
#from PMS.Network import *
#from OpenSSL import SSL
#import socket

class nntpClient(nntpObj):
  def __init__(self):
    funcName = '[nntpClient.init]'
    self.lock = Thread.Lock()
    if self.nntpSSL:
      log(5, funcName, 'Initializing SSL Socket')
      self.sock = Network.SSLSocket()
      log(5, funcName, 'SSL Socket initialized')
    else:
      log(5, funcName, 'Initializing socket')
      self.sock = Network.Socket()
      log(5, funcName, 'Socket initializied')
      
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
      log(6, funcName, "Downloading article '%s'", article_obj.article_id)
      self.send_command('body <%s>', article_obj.article_id)
    
      lines = []
      data = ''
      while True:
        chunk = self.sock.recv(32768)
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