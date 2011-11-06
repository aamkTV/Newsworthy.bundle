from configuration import *
from common import *
import sys
import traceback

DOWNLOAD_MEASURE_TIME = 1 # Number of seconds over which to average download speeds
RETRY_DELAY = 0

class nntpManager(AppService):
  #AppService __init__ calls this
  def init(self):
    self.clients = []
    self.current_server = None
    self.get_server_lock = Thread.Lock()
    self.count_lock = Thread.Lock()
    self.get_available_conn_lock = Thread.Lock()
    self.startup_clear_nntp_connections()
  
  def startup_clear_nntp_connections(self):
    funcName = '[nntpManager.startup_clear_nntp_connections]'
    for server_id in self.servers:
      server = self.servers[server_id]
      connections_to_clear = server.connections_in_use - self.clients_with_server(server)
      for i in range(connections_to_clear):
        server.releaseConnection()
  
  def clients_with_server(self, server):
    funcName ='[nntpManager.clients_with_server]'
    num_clients = 0
    try:
      for client in self.clients:
        if client.nntp_server == server:
          num_clients += 1
    except:
      log(3, funcName, 'Unable to count clients for', server)
    return num_clients
    
  @property
  def servers(self):
    return self.app.cfg.nntp
    
  ################################################################################ 
  def get_client(self, nntp):
    funcName = '[nntpManager.get_connection]'
    server = nntpClient(self.app)
    server.nntp_server = nntp
    return server
  ################################################################################ 
  def get_available_client(self, wait=False):
    funcName = '[nntpManager.get_available_connection]'
    log(8, funcName, 'Looking for an available connection')
    if self.connections_available:
      Thread.AcquireLock(self.get_available_conn_lock)
      nntp = None
      try:
        #nntp = nntpClient(self.app)
        server_wanted, usedList = self.get_next_server()
        nntp = self.get_client(server_wanted)
      except:
        ex, err, tb = sys.exc_info()
        log(1, funcName, 'Could not get a connection:', err)
        if nntp: self.deregister(nntp)
        raise nntpException('Unable to get a connection', 1001)
      finally:
        Thread.ReleaseLock(self.get_available_conn_lock)
    else:
      log(3, funcName, 'No connections available')
      raise nntpException('No connections available', 1002)
    return nntp    
  ################################################################################ 
  @property
  def connections_available(self):
    funcName = '[nntpManager.connections_available]'
    Thread.AcquireLock(self.count_lock)
    available_connections = 0
    try:
      for server_id in self.servers:
        available_connections += self.servers[server_id].connections_available
    except:
      ex, err, tb = sys.exc_info()
      log(1, funcName, 'Error when looking for connections:', err)
    finally:
      Thread.ReleaseLock(self.count_lock)
    return available_connections
  ################################################################################ 
  def register(self, client):
    funcName = '[nntpManager.register]'
    log(7, funcName, 'Registering a client')
    self.clients.append(client)
    #client.nntp_server.useConnection()
  
  ################################################################################  
  def deregister(self, client):
    funcName = '[nntpManager.deregister]'
    log(7, funcName, 'Deregistering a client')
    self.clients.remove(client)
    client.nntp_server.releaseConnection()
  
  ################################################################################  
  def __str__(self):
    return str(self.clients)
    
  ################################################################################ 
  def disconnect_all(self):
    funcName = '[nntpManager.disconnect_all]'
    for client in self.clients:
      try:
        client.disconnect()
      except:
        log(3, funcName, 'Unable to disconnect a client connection')

  ################################################################################ 
  def get_server_by_id(self, id):
    """Gets a server by the id passed in by the caller"""
    funcName = '[nntpManager.get_server_by_id]'
    try:
      int(id)
    except:
      raise Exception("Not a valid number: " + str(id))
    if id <= 0: raise Exception("Not a valid server id: " + str(id))
    
    log(6, funcName, 'Looking for server id:', id)
    server_wanted = None
    for server_id in self.servers:
      if int(server_id) == int(id):
       server_wanted = self.servers[server_id]
       log(6, funcName, 'Returning server:', server_wanted)
       break
    return server_wanted
  
  ################################################################################
  def get_server_by_priority(self, priority=None, usedList=None, try_again=False):
    """Gets a server by the priority passed in by the caller"""
    funcName = '[nntpManager.get_server_by_priority]'
    try:
      int(priority)
    except:
      raise Exception("Not a valid number: " + str(priority))
    if priority <= 0: raise Exception("Not a valid server priority: " + str(priority))
    
    server_wanted = None
    if not try_again:
      log(8, funcName, 'Waiting on self.get_server_lock')
      Thread.AcquireLock(self.get_server_lock)
      log(8, funcName, 'Got the lock')
      
    server_unavailable = False
    
    try:
      for server_id in self.servers:
        server = self.servers[server_id]
        log(8, funcName, 'Checking server:', server, 'against', priority)
        if usedList:
          if server_id in usedList:
            log(8, funcName, 'Already used:', server)
            continue
        #server = self.servers[server_id]
        if (int(server.priority) == int(priority)):
          if not ((server.test_passed) and (server.connections_available)):
            log(3, funcName, 'Can not use server:', server, ': Tested:', server.test_passed, ', connections_available:', server.connections_available)
            server_unavailable = True
            continue
          log(8, funcName, 'Matching priority server found:', server)
          server_wanted = server
          break
        if server_unavailable and not server_wanted:
          next_priority = self.get_next_priority(priority)
          server_wanted = self.get_server_by_priority(next_priority, usedList, try_again=True)
    except:
      ex, err, tb = sys.exc_info()
      log(1, funcName, 'Error:', err)
    finally:
      if not try_again: Thread.ReleaseLock(self.get_server_lock)
    
    return server_wanted
  
  ################################################################################
  def get_next_server(self, in_server=None, usedList=None):
    """Gets the next server.  First we look for servers with the same priority, then lower priority.
    If a usedList is specified, the current server must also be specified."""
    funcName = '[nntpManager.get_next_server]'
    if usedList and not in_server:
      raise Exception('usedList included, but did not specify which server you are currently using')
    
    server_wanted = None
    if not usedList:
      usedList = []
    
    # mark the server as used
    if in_server:
      if in_server.id not in usedList: usedList.append(in_server.id)
      log(7, funcName, 'usedList:', usedList)
      in_server_priority = in_server.priority
    else:
      in_server_priority = int(1)
    
    # First, see if there are any servers of the same priority to use
    log(8, funcName, 'Checking for more servers with priority:', in_server_priority)
    server_wanted = self.get_server_by_priority(priority = in_server_priority, usedList = usedList)
    if server_wanted:
      log(8, funcName, 'This server found with the same priority:', server_wanted)
    
    # Second, find a lower priority server to use
    if not server_wanted:
      log(8, funcName, 'Checking for the next priority server level')
      next_priority = self.get_next_priority(priority = in_server_priority)
      log(7, funcName, 'Looking for servers with priority:', next_priority)
      if next_priority > 0:
        server_wanted = self.get_server_by_priority(priority = next_priority, usedList = usedList)
    log(8, funcName, 'This server:', server_wanted)
    return server_wanted, usedList
  
  ################################################################################
  def get_next_priority(self, priority):
    funcName = '[nntpManager.get_next_priority]'
    log(8, funcName, 'Looking for something other than:', priority)
    p = 0
    for server_id in self.servers:
      server = self.servers[server_id]
      #log(8, funcName, 'Checking this server:', server)
      #log(8, funcName, 'Comparing server', server, 'priority against priority:', server.priority,':',priority)
      if server.priority > priority:
        if p == 0:
          p = server.priority
        if server.priority < p:
          p = server.priority
    return p
        
  ################################################################################
  @property
  def speed(self):
    speed = 0
    for client in self.clients:
      clientSpeed = float(client.downloaded_bytes) / float((client.finish_download_time - client.start_download_time).seconds)
      speed += clientSpeed
    return speed
    
##################################################################################
class nntpClient(AppService):
  def init(self):
    funcName = '[nntpClient.init]'
#    log(7, funcName, 'self:', self)
#    self.app = app
    self.lock = Thread.Lock()
    self.byte_lock = Thread.Lock()
    self.speed_lock = Thread.Lock()
    self.nntpManager = self.app.nntpManager
    self.nntpManager.register(self)
#     self.speed = 0
#     self.downloaded_bytes = 0
#     self.start_download_time = Datetime.Now()
#     self.finish_download_time = None
    self.retries = 0
    self.max_retries = 1
    self.timeout = 2
    self.monitor_speed = True
    #self.server_list = self.nntpManager.servers
    #if len(self.nntpManager.servers):
    #  self.nntp_server, self.usedList = self.nntpManager.get_next_server()
    #  if self.nntp_server: self.create_sock()
    self.usedList = []
    self.nntp_server = None
    self.server_failures = 0
    self.original_server_id = 0
    
  ################################################################################ 
  def create_sock(self):
    funcName = '[nntpClient.create_sock]'
    try:
      if self.nntp_server.nntpSSL:
        log(6, funcName, 'Initializing SSL Socket')
        self.sock = Network.SSLSocket()
        log(6, funcName, 'SSL Socket initialized')
      else:
        log(6, funcName, 'Initializing socket')
        self.sock = Network.Socket()
        log(5, funcName, 'Socket initializied')
      self.nntp_server.useConnection()
      self.speed = 0
      self.downloaded_bytes = 0
      self.start_download_time = Datetime.Now()
      self.finish_download_time = None
    except:
      self.nntp_server, self.usedList = self.nntpManager.get_next_server(self.nntp_server, self.usedList)
      if self.nntp_server:
        self.create_sock()
      else:
        raise nntpException("Could not create a socket connection", 1000)

  ################################################################################
  def connect(self):
    funcName='[nntpClient.connect]'
    if not self.nntp_server: self.nntp_server, self.usedList = self.nntpManager.get_next_server(self.usedList)
    self.create_sock()
    Thread.AcquireLock(self.lock)
    self.sock.setblocking(0)
    self.sock.settimeout(5)
    log(5, funcName, 'Attempting to connect to', self.nntp_server)
    try:
      self.sock.settimeout(self.timeout)
      self.sock.connect((self.nntp_server.nntpHost, int(self.nntp_server.nntpPort)))
      if self.nntp_server.nntpSSL:
        self.sock.do_handshake()

      log(5, funcName, 'Successfully connected')
      # Check that the server is ready
      status_line = self.read_line()
      log(7, funcName, 'Status_line:', status_line)
      if status_line[0:3] != '200':
        raise Exception("Bad status")

      # Try to log in
      self.send_command('authinfo user %s', self.nntp_server.nntpUsername)
      status_line = self.read_line()
      if status_line[0:3] != '381':
        raise Exception("Bad username")
    
      self.send_command('authinfo pass %s' % self.nntp_server.nntpPassword)
      status_line = self.read_line()
      if status_line[0:3] != '281':
        raise Exception("Bad password")
        
      log(5,funcName,"Successfully connected to", self.nntp_server.nntpHost, 'as', self.nntp_server.nntpUsername)
      self.sock.setblocking(1)
      return True
    except:
      return False
    finally:
      Thread.ReleaseLock(self.lock)
      self.monitor_speed = True
  
  ################################################################################ 
  def article_exists(self, article_id):
    funcName = '[nntpClient.article_exists]'
    exists = False
    log(7, funcName, 'checking if article exists:', article_id)
    self.send_command('body <%s>', article_id)
    data = self.sock.recv(256)
    if data[:3] != '430':
      exists = True
    self.flush()
    return exists
  
  ################################################################################
  def disconnect(self):
    funcName = '[nntpClient.disconnect]'
    #self.sock.disconnect()
    try:
      self.send_command('QUIT')
    except:
      log(5, funcName, 'Error sending QUIT command to', self.nntp_server)
    
    try:
      self.sock.close()
    except:
      log(5, funcName, 'Error closing socket for', self.nntp_server)
    finally:
      self.sock = None
    
    try:
      self.app.nntpManager.deregister(self)
    except:
      log(5, funcName, 'Error deregistering:', self.nntp_server)
#    finally:
#      self.sock.close()
#      self.app.nntpManager.deregister(self)

      
    #self.monitor_speed = False
     
  ################################################################################
  def send_command(self, command, *args):
    try:
      self.sock.sendall((command % args) + '\r\n')
      return True
    except:
      return False
    
  ################################################################################ 
  def read_line(self):
    data = self.sock.recv(1024)
    lines = data.split('\r\n')
    data = lines.pop()
    return lines[0]
  
  ################################################################################
  def flush(self):
    funcName = '[nntpClient.nntpClient.flush]'
    data = ''
    while True:
      self.flush_times = self.flush_times + 1
      #log(9, funcName, 'flushing:', self.flush_times)
      data = self.sock.recv(999999)
      lines = data.split('\r\n')
      #log(9, funcName, 'last lines:', lines[-5:-1])
      #log(9, funcName, 'len(lines):', len(lines), 'lines[-1]:', lines[-1])
      if len(lines) > 0 and ('.' in lines[-2:-1] ):
        break
    log(8, funcName, 'end!')
      
  ################################################################################ 
  def get_article(self, article_obj, retry_attempt=False):
    funcName = '[nntpClient.nntpClient.get_article][' + str(article_obj.segment_number) + ']'
    retry = False
    Thread.AcquireLock(self.lock)
    try:
      #if not self.article_exists(article_obj.article_id): raise ('Article Not Found', 430)
      log(9, funcName, "Downloading article:", article_obj.article_id)
      sent = self.send_command('body <%s>', article_obj.article_id)
      if sent:
        log(9, funcName, "Data Sent") 
      else:
        log(3, funcName, 'Error sending data')
        
    
      lines = []
      data = ''
      self.downloaded_bytes = 0

      try:
        while True:
          if self.start_download_time == 0: self.start_download_time = Datetime.Now()
          #log(9, funcName, 'Receiving data')
          try:
            chunk = self.sock.recv(32768)
          except:
            chunk = ""
          #log(9, funcName, 'Data Received')
          if not len(chunk) or chunk[:3] == '430':
            raise nntpException('Article Not Found', 430)
          
          # test of the system
          # find this in common.py now.  test_article_failure = [32, 33]
          if ((article_obj.segment_number in test_article_failure) and (self.nntp_server.nntpHost in test_server_failure)):
            log(2, funcName, 'Simulating error on segment', test_article_failure)
            self.flush_times = 0
            self.flush()
            log(7, funcName, 'Done flushing!')
            raise nntpException('Article Not Found', 430)
              
          self.finish_download_time = Datetime.Now()
          
          #try:
          #  Thread.AcquireLock(self.byte_lock)
          self.downloaded_bytes = self.downloaded_bytes + len(chunk)
          #except:
          #  pass
          #finally:
          #  Thread.ReleaseLock(self.byte_lock)
          
          #log(7, funcName, 'elapsed time:', ((self.finish_download_time - self.start_download_time).seconds), 'downloaded bytes:', self.downloaded_bytes)
          if ((self.finish_download_time - self.start_download_time).seconds) >= DOWNLOAD_MEASURE_TIME:
            #self.speed = float(self.downloaded_bytes) / float((self.finish_download_time - self.start_download_time).seconds)
            #log(9, funcName, 'speed:', self.speed)
            self.start_download_time = 0
            self.downloaded_bytes = 0
          data += chunk
          new_lines = data.split('\r\n')
          data = new_lines.pop()
          lines.extend(new_lines)
          
          #if len(lines) > 0 and (lines[-1] == '.' or lines[-2] == '.'):
          if len(lines) > 0 and lines[-1] == '.':
            break
        log(8, funcName, 'Segment complete using server:', self.nntp_server)
        return lines[1:-1]
      #except nntpException:
      #  type, exception, traceback = sys.exc_info()
      #  if exception.id == 430:
      #    raise
      #  else:
      #    log(1, funcName, 'nntp error, id:', id, ', mesg:', mesg, ', tb:', traceback.format_exc())
      except:
        retry = True
        Thread.ReleaseLock(self.lock)
        if not retry_attempt:
          log(5, funcName, 'FAILED, awaiting retry')
          data = self.retry(article_obj)
          if data:
            log(5, funcName, 'Data received from retry, returning')
            return data
        else:
          raise
        
        #error, msg, tb = sys.exc_info()
        #if self.retries < self.max_retries:
        #  log(2, funcName, 'exception:', error, ', msg:', msg)#, 'tb:', traceback.format_exc())
        #  log(2, funcName, 'Error downloading, retrying article:', article_obj.article_id)
        #  retry = True
        #  Thread.ReleaseLock(self.lock)
        #  return self.retry(article_obj)
        #else:
        #  log(1, funcName, 'Connection reset by peer, retried', self.max_retries, 'times, no luck')
        #  # skip it yo
        #  raise nntpException('Article Not Found', 430)
        #else:
        #  raise
    finally:
      if not retry: Thread.ReleaseLock(self.lock)
      self.retries = 0
      pass
  
  ################################################################################ 
  def speed_monitor(self):
    funcName = '[nntpclient.nntpClient.speed_monitor]'
    while True:
      if not monitor_speed: break
      try:
        Thread.AcquireLock(self.byte_lock)
        if ((self.finish_download_time - self.start_download_time).seconds) >= DOWNLOAD_MEASURE_TIME:
          self.speed = float(self.downloaded_bytes) / float((self.finish_download_time - self.start_download_time).seconds)
          log(8, funcName, 'speed:', self.speed)
          self.start_download_time = Datetime.Now()
          self.downloaded_bytes = 0
      except:
        self.speed = 0
      finally:
        Thread.ReleaseLock(self.byte_lock)
      
  ################################################################################
  def retry(self, article_obj):
    funcName = '[nntpclient.nntpClient.retry]'
    # Starting with the current server, then looping through each server, retry the article self.retries number of times
    if self.original_server_id == 0:
      log(8, funcName, 'Setting self.original_server_id to:', self.nntp_server.id)
      self.original_server_id = self.nntp_server.id
    
    server_to_try = nntpClient(self.app)
    server_to_try.nntp_server = self.nntp_server
    server_config_to_try = self.nntp_server
    usedList = []
    data = None
    
    while (len(self.usedList) <= len(self.nntpManager.servers)) and (server_config_to_try):
      
      log(7, funcName, 'Trying', self.max_retries, 'times on', server_to_try.nntp_server)
      
      for i in range(self.max_retries):
        
        try:
          self.retries = i
          log(7, funcName, 'Number of retries so far:', self.retries)
          #server_to_try.create_sock()
          server_to_try.connect()
          data = server_to_try.get_article(article_obj, retry_attempt=True)
          log(7, funcName, 'RETRY Successful')
        except:
          ex, err, tb = sys.exc_info()
          log(7, funcName, 'Error when retrying:', err)
        finally:
          server_to_try.disconnect()
        
        if data:
          log(7, funcName, 'Returning data')
          return data
          break
      
      # If we get this far, we have tried self.max_retries times and still haven't returned anything
      log(7, funcName, 'Tried', self.retries, 'times for server', server_to_try.nntp_server)
      # Get the next server, if available
      server_config_to_try, usedList = self.nntpManager.get_next_server(server_to_try.nntp_server, usedList)
      log(7, funcName, 'Next server to try:', server_config_to_try)
      server_to_try = nntpClient(self.app)
      server_to_try.nntp_server = server_config_to_try
    
    #If we get this far, we tried all retries and all servers, and still didn't get it
    if not data: raise nntpException('Article Not Found', 430)
