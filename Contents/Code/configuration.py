#from common import *
import random
import sys
import fileSystem
from nntpclient import nntpClient
app = None

class configuration(AppService):
	def init(self):
		funcName = '[configuration.init]'
		global app
		app = self.app
	
	def checkDict(self, dict):
		funcName = '[configuration.checkDict]'
		if not dict in Dict:
			log(3, funcName, 'Creating dict:', dict)
			Dict[dict] = {}
			#Dict.Save()
			return True
		
	def get_nntp(self):
		self.checkDict(nntpConfigDict)
		return Dict[nntpConfigDict]
	def set_nntp(self, nntpDict):
		self.my_nntp = nntpDict
		Dict[nntpConfigDict] = nntpDict
		#Dict.Save()
	nntp = property(get_nntp, set_nntp)
	
	def get_nzb(self):
		self.checkDict(nzbConfigDict)
		return Dict[nzbConfigDict]
	def set_nzb(self, nzbDict):
		self.my_nzb = nzbDict
		Dict[nzbConfigDict] = nzbDict
		#Dict.Save()
	nzb = property(get_nzb, set_nzb)
	
	def get_fs(self):
		self.checkDict(FSConfigDict)
		return Dict[FSConfigDict]
	def set_fs(self, fsDict):
		self.my_fs = fsDict
		Dict[FSConfigDict] = fsDict
		#Dict.Save()
	fs = property(get_fs, set_fs)
	
	def get_nntpSettings(self):
		self.checkDict(nntpSettingDict)
		return Dict[nntpSettingDict]
	def set_nntpSettings(self, nntpSettings):
		Dict[nntpSettingDict] = nntpSettings
		#Dict.Save()
	nntpSettings = property(get_nntpSettings, set_nntpSettings)

connection_use_lock = Thread.Lock()			
class nntpServer(object):
	def __init__(self):
		self.username = "<not set>"
		self.password = "<not set>"
		self.host = "<not set>"
		self.port = 563
		self.ssl = True
		self.connections = 5
		self.priority = 10
		self.test_passed = False
		self.myid = random.randint(1, 1000000)
		self.connections_in_use = 0
		
	def setUsername(self, query):
		self.username = query
		self.test_passed = False
		self.save()
	def setPassword(self, query):
		self.password = query
		self.test_passed = False
		self.save()
	def setHost(self, query):
		Log('Setting host to ' + query)
		self.host = query
		self.test_passed = False
		self.save()
	def setPort(self, query):
		try:
			self.port = int(query)
			self.test_passed = False
			self.save()
		except ValueError:
			raise Exception("Not a number")
	def setSSL(self, query):
		self.ssl = bool(query)
		self.test_passed = False
		self.save()
	def toggleSSL(self):
		if self.ssl:
			self.setSSL(False)
		else:
			self.setSSL(True)
		self.test_passed = False
	def setConnections(self, query):
		try:
			self.connections = int(query)
			self.save()
		except ValueError:
			raise Exception("Not a number")
	def setPriority(self, query):
		try:
			self.priority = int(query)
			self.save()
		except ValueError:
			raise Exception("Not a number")
	def useConnection(self):
		funcName = '[nntpServer.useConnection]'
		log(8, funcName, 'Acquiring connection use lock for server:', self)
		Thread.AcquireLock(connection_use_lock)
		self.connections_in_use = self.connections_in_use + 1
		log(8, funcName, self, 'Connections in use:', self.connections_in_use)
		Thread.ReleaseLock(connection_use_lock)
	def releaseConnection(self):
		funcName = '[nntpServer.releaseConnection]'
		Thread.AcquireLock(connection_use_lock)
		self.connections_in_use = self.connections_in_use - 1
		log(8, funcName, self, 'Connections in use:', self.connections_in_use)
		Thread.ReleaseLock(connection_use_lock)
		self.save()
	
	@property
	def connections_available(self):
		Thread.AcquireLock(connection_use_lock)
		answer = ((self.connections - self.connections_in_use) and not (self.connections_in_use > self.connections))
		Thread.ReleaseLock(connection_use_lock)
		return answer
	
	def __repr__(self):
		return str(self.username) + "@" + str(self.nntpHost) + ":" + str(self.nntpPort) + " (P" + str(self.priority) + "/Conn:" + str(self.connections_in_use) + "/" + str(self.nntpConnections) + ")"# + (" ID:" + str(self.id) + ")"
	@property
	def name(self):
		return str(self)
	@property
	def id(self):
		return self.myid
	@property
	def nntpUsername(self):
		return self.username
	@property
	def nntpPassword(self):
		return self.password
	@property	
	def nntpHost(self):
		return self.host
	@property
	def nntpPort(self):
		return self.port
	@property
	def nntpSSL(self):
		return self.ssl
	@property
	def nntpConnections(self):
		return self.connections
	@property
	def nntpPriority(self):
		return self.priority
	
	def test_connection(self):
		funcName = '[nntpServer.test_connection]'
		test_client = nntpClient(app)
		#test_client.sock.close()
		test_client.nntp_server = test_client.nntpManager.get_server_by_id(self.id)
		#test_client.create_sock()
		test_response = test_client.connect()
		if test_client: test_client.disconnect()
		if test_response:
			self.test_passed = True
		else:
			self.test_passed = False
		return self.test_passed
		
	def save(self):
		nntpDict = Dict[nntpConfigDict]
		nntpDict[self.id] = self
		Dict[nntpConfigDict] = nntpDict
		#Dict.Save()

@route(routeBase + 'save_server_setting/{server_id}/{key}/{query}')
def save_server_setting(sender=None, server_id=None, key=None, query=None):
	funcName = '[configuration.save_server_setting]'
	nntpDict = Dict[nntpConfigDict]
	server = None
	for nntp in nntpDict:
		#log(1, funcName, nntp)
		server = nntpDict[nntp]
		if server.id == server_id:
			log(3, funcName, 'Updating server id', server.id, key, 'to', query)
			try:
				if key == "host":
					server.setHost(query)
				elif key == "username":
					server.setUsername(query)
				elif key == "password":
					server.setPassword(query)
				elif key == "port":
					server.setPort(query)
				elif key == "ssl":
					server.setSSL(query)
				elif key == "toggleSSL":
					server.toggleSSL()
				elif key == "connections":
					server.setConnections(query)
				elif key == "priority":
					server.setPriority(query)
				return True
			except:
				errmsg = sys.exc_info()[1]
				return MessageContainer("Failed to save", "Error when trying to save your value: " + str(errmsg))
		if not server: return MessageContainer("Failed to save", "Could not find server to save.")

@route(routeBase + 'save_max_connections_setting/{query}')
def save_max_connections_setting(sender=None, query=None, resetDownloads=True):
	funcName = '[configuration.save_max_connections_setting]'
	try:
		int(query)
	except ValueError:
		raise Exception('Not a number')
	
	total_connections = 0
	try:
		for server_id in app.nntpManager.servers:
			total_connections += app.nntpManager.servers[server_id].nntpConnections
	except:
		log(3, funcName, 'Unable to count total connections')
	
	if int(query) > total_connections:
		return MessageContainer("Too many connections", "You are attempting to use more connections than are available based on your server configurations.  You have " + str(total_connections) + " configured.")
	
	elif int(query) == total_connections and total_connections != 0:
		conn_used = int(int(query)-1)
		setDictField(theDict=nntpSettingDict, key='TotalConnections', query=conn_used, sender=None)
		app.num_client_threads = conn_used
		if resetDownloads: resetDownloader()
		return MessageContainer("Saved with changes", "Set the total number to " + str(conn_used) + " to allow for connection testing.")
	
	else:
		conn_used = int(query)
		setDictField(theDict=nntpSettingDict, key='TotalConnections', query=conn_used, sender=None)
		app.num_client_threads = conn_used
		if resetDownloads: resetDownloader()
		if conn_used == 0:
			return MessageContainer("Warning", "0 connections will be used; nothing will download.")

@route(routeBase + 'manageNNTPs')
def manageNNTPs():
	funcName = '[configuration.manageNNTPs]'

	cm = ContextMenu(includeStandardItems=False)
	cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
	dir = MediaContainer(viewGroup='Lists', replaceParent=False, noHistory=False, contextMenu=cm, noCache=True, thumb=R('configuration.png'))
	
	dir.Append(DirectoryItem(Route(addNewNNTPServer), title="Add a News Server", thumb=R('plus_green.png'), contextKey='a', contextArgs={}))
	dir.Append(Function(InputDirectoryItem(save_max_connections_setting, title=("Total NNTP Connections to use: " + str(getConfigValue(theDict=nntpSettingDict, key='TotalConnections'))), prompt="Set the total number of connections to use", contextKey="a", contextArgs={})))
	#dir.Append(InputDirectoryItem(Route(save_max_connections_setting), title=("Total NNTP Connections to use: " + str(getConfigValue(theDict=nntpSettingDict, key='TotalConnections'))), prompt="Set the total number of connections to use", contextKey="a", contextArgs={}))
	#dir.Append(Function(InputDirectoryItem(setDictField, title=("Total connections to use: " + str(getConfigValue(theDict=nntpSettingDict, key='TotalConnections'))), prompt="Set the total number of connections to use", contextKey="a", contextArgs={}), theDict=nntpSettingDict, key='TotalConnections'))
	#dir.Append(Function(DirectoryItem(configureNNTP, title="Add a News Server"), id=None))
	nntpDict = Dict[nntpConfigDict]
	log(1, funcName, nntpDict)
	if len(nntpDict) > 0:
		for server in nntpDict:
			server = nntpDict[server]
			#name = str(server.username) + "@" + str(server.host) + ":" + str(server.port)
			if server.test_passed:
				server_thumb = 'check_green.png'
			else:
				server_thumb = 'x_red.png'
			dir.Append(DirectoryItem(Route(configureNNTP, id=server.id), title=server.name, thumb=R(server_thumb), contextKey='a', contextArgs={}))
	return dir

@route(routeBase + 'addNewNNTPServer')
def addNewNNTPServer():
	funcName = '[configuration.addNewNNTPServer]'
	server = nntpServer()
	server.save()
	log(3, funcName, 'New server ID:', server.id)
	#return configureNNTP(server.id)
	
@route(routeBase + 'configureNNTP/{id}')
def configureNNTP(id=0):
	funcName = '[configuration.configureNNTP]'

	cm = ContextMenu(includeStandardItems=False)
	cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
	id=int(id)
	log(4, funcName, 'id:', id)
	
	server = None
	
	if id != 0:
		log(6, funcName, 'looking for existing nntp config with id:', id)
		nntpDict = Dict[nntpConfigDict]
		for svr in nntpDict:
			log(7, funcName, 'Examining server:', svr)
			svr = nntpDict[svr]
			if id == svr.id:
				server = svr
				log(6, funcName, 'Found server:', svr)
				break
	if not server:
		return manageNNTPs()
		
	dir = MediaContainer(viewGroup='Lists', replaceParent=False, noHistory=False, noCache=True, thumb=R('configuration.png'), contextMenu=cm)
	
	#dir.Append(InputDirectoryItem(Route(save_server_setting, server_id=server.id, key='host'), title=(L("News Server") + ": " + server.host), prompt=L("Set News Server Host")))
	dir.Append(Function(InputDirectoryItem(save_server_setting, title=(L("News Server") + ": " + server.host), prompt=L("Set News Server Host")), server_id=server.id, key="host"))
	dir.Append(Function(InputDirectoryItem(save_server_setting, title=(L("News Server Port") + ": " + str(server.port)), prompt=L("Set News Server Port")), server_id=server.id, key="port"))
	dir.Append(Function(DirectoryItem(save_server_setting, title=(L("News Server SSL?") + ": " + str(server.ssl))), server_id=server.id, key="toggleSSL"))
	dir.Append(Function(InputDirectoryItem(save_server_setting, title=(L("News Server Username") + ": " + server.username), prompt=L("Set News Server Username")), server_id=server.id, key="username"))
	if server.password == "<not set>":
		dir.Append(Function(InputDirectoryItem(save_server_setting, title=(L("News Server Password") + ": " + server.password), prompt=L("Set News Server Password")), server_id=server.id, key="password"))
	else:
		dir.Append(Function(InputDirectoryItem(save_server_setting, title=(L("News Server Password") + ": *********"), prompt=L("Set News Server Password")), server_id=server.id, key="password"))
	
	dir.Append(Function(InputDirectoryItem(save_server_setting, title=(L("Number of Connections Available") + ": " + str(server.connections)), prompt=L("Set the number of NNTP connections available")), server_id=server.id, key="connections"))
	dir.Append(Function(InputDirectoryItem(save_server_setting, title=(L("Priority") + ": " + str(server.priority)), prompt=L("Set the priority for this server")), server_id=server.id, key="priority"))
	
	#Create a test function
	if id != 0: dir.Append(DirectoryItem(Route(testNNTP, id=server.id), title=L("Test this server")))
	if id != 0: dir.Append(DirectoryItem(Route(deleteNNTP, id=server.id), title=L("Delete this server configuration")))
	
	if id != 0: return dir

######################################################################################
@route(routeBase + 'testNNTP/{id}')
def testNNTP(id):
	if not app:
		return MessageContainer("No app", "No application to use")
	server = app.nntpManager.get_server_by_id(id)
	if not server:
		return MessageContainer("Server Error", "Error when testing.  This may not be related to your configuration.")
	result = server.test_connection()
	if result:
		return MessageContainer("Successfully connected", "The connection was successful")
	else:
		return MessageContainer("Dismal failure", "The connection failed")
######################################################################################
@route(routeBase + 'deleteNNTPUI/{id}')
def deleteNNTPUI(id):
	deleteNNTP(id)
	Redirect(manageNNTPs())
	
@route(routeBase + 'deleteNNTP/{id}')
def deleteNNTP(id):
	funcName = '[deleteNNTP]'
	log(5, funcName, 'Deleting server ID:', id)
	nntpDict = Dict[nntpConfigDict]
	del nntpDict[int(id)]
	Dict[nntpConfigDict] = nntpDict
	Dict.Save()
	log(5, funcName, 'Server deleted:', id)
	return MessageContainer("Success", "Server successfully deleted.")
	
@route(routeBase + 'configure')
def configure(sender):
	funcName = "[configuration.configure]"
	
	# Make sure the dictionaries exist for the configuration needs
 	if nzbConfigDict in Dict:
 		pass
 	else:
 		log(3, funcName, 'nzbConfigDict not found, creating it')
 		Dict[nzbConfigDict]= {}
 	nzbConfig = Dict[nzbConfigDict]
	
	if FSConfigDict in Dict:
		pass
	else:
		log(3, funcName, 'FSConfigDict was not found, creating it')
		Dict[FSConfigDict] = {}
	FSConfig = Dict[FSConfigDict]
	
#	nntp = nntpServer()
	
	cm = ContextMenu(includeStandardItems=False)
	cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
	dir = MediaContainer(contextMenu=cm, viewGroup='Lists', replaceParent=False, noHistory=False, noCache=True, thumb=R('configuration.png'))
	
	###########################
	# NZB CONFIGURATION SECTION
	# Present the user with the options to configure their nzb service info
	
	###########################
	# NZBMatrix Configs
	if Prefs['NZBService'] == 'NZBMatrix' or True:
		dir.Append(Function(InputDirectoryItem(setDictField, title=("NZBMatrix Username: " + getConfigValue(theDict=nzbConfigDict, key='nzbMatrixUsername')), prompt=("Set NZBMatrix Username"), contextKey="a", contextArgs={}), theDict=nzbConfigDict, key='nzbMatrixUsername'))
		if len(getConfigValue(theDict=nzbConfigDict, key='nzbMatrixPassword'))>=1:
			dir.Append(Function(InputDirectoryItem(setDictField, title=("NZBMatrix Password: ******"), prompt=("Set NZBMatrix Password"), contextKey="a", contextArgs={}), theDict=nzbConfigDict, key='nzbMatrixPassword'))
		else:
			dir.Append(Function(InputDirectoryItem(setDictField, title=("NZBMatrix Password: <Not Set>"), prompt=("Set NZBMatrix Password"), contextKey="a", contextArgs={}), theDict=nzbConfigDict, key='nzbMatrixPassword'))
		########################
		# I haven't found a use for the nzbmatrix api key in this app.
		# You can always enable this input if you see need for it.
		########################
		#dir.Append(Function(InputDirectoryItem(setDictField, title=("NZBMatrix API Key: " + getConfigValue(theDict=nzbConfigDict, key='nzbMatrixAPIKey')), prompt=L("Set NZBMatrix API Key"), contextKey="a", contextArgs={}), theDict=nzbConfigDict, key='nzbMatrixAPIKey'))			
	
	##########################
	# Newzbin Configs
	if Prefs['NZBService'] == 'Newzbin' or True:
		dir.Append(Function(InputDirectoryItem(setDictField, title=("Newzbin Username: " + getConfigValue(theDict=nzbConfigDict, key='newzbinUsername')), prompt=("Set Newzbin Username"), contextKey="a", contextArgs={}), theDict=nzbConfigDict, key='newzbinUsername'))
		if len(getConfigValue(theDict=nzbConfigDict, key='newzbinPassword'))>=1:
			dir.Append(Function(InputDirectoryItem(setDictField, title=("Newzbin Password: ******"), prompt=("Set Newzbin Password"), contextKey="a", contextArgs={}), theDict=nzbConfigDict, key='newzbinPassword'))
		else:
			dir.Append(Function(InputDirectoryItem(setDictField, title=("Newzbin Password: <Not Set>"), prompt=("Set Newzbin Password"), contextKey="a", contextArgs={}), theDict=nzbConfigDict, key='newzbinPassword'))
			
	##########################################
	# NNTP (News Server) CONFIGURATION SECTION
	# Present the user with the options to configure their news servers
	dir.Append(DirectoryItem(Route(manageNNTPs), title=L("Manage News Servers"), thumb=R('configuration.png'), contextArgs={}, contextKey='a'))
	 
	##################################
	# Filesystem configuration section
	# Ask the user where they want to save the files
	dir.Append(DirectoryItem(Route(manageFolders), title=L("Manage Filesystem Folders"), thumb=R('configuration.png'), contextArgs={}, contextKey='a'))
	#dir.Append(Function(InputDirectoryItem(setDictField, title=("Download To (i.e. Temp): " + getConfigValue(theDict=FSConfigDict, key='downloadDir')), prompt="Set the download directory", contextKey="a", contextArgs={}), theDict=FSConfigDict, key='downloadDir'))
	#dir.Append(Function(InputDirectoryItem(setDictField, title=("Archive To: " + getConfigValue(theDict=FSConfigDict, key='archiveDir')), prompt="Set the download archive directory", contextKey="a", contextArgs={}), theDict=FSConfigDict, key='archiveDir'))
	#dir.Append(Function(DirectoryItem(ToggleValue, title=("Auto Archive? " + str(getConfigValue(theDict=FSConfigDict, key='autoArchive'))), prompt="Auto Archive Downloads?", contextKey="a", contextArgs={}), theDict=FSConfigDict, key='autoArchive'))
	 
	return dir
	
############################################################################
@route(routeBase + 'manageFolders')
def manageFolders(folder=None):
	FS = fileSystem.FS()
	cm = ContextMenu(includeStandardItems=False)
	#cm.Append(Function(DirectoryItem(selectFolder, title=L('SET_DL_FOLDER')), folder=pass))
	dir = MediaContainer(contextMenu=cm, viewGroup='Lists', replaceParent=False, noHistory=False, noCache=True)
  
	if folder != None:
		folder_listing = FS.show_folder_contents(folder)
	else:
		folder = FS.root_folder
		folder_listing = FS.show_folder_contents(FS.root_folder)

	for item in folder_listing:
		full_item_path = Core.storage.join_path(folder, item)
		if Core.storage.dir_exists(full_item_path):
			item_cm = ContextMenu(includeStandardItems=False)
			item_cm.Extend(cm)
			item_cm.Append(Function(DirectoryItem(selectFolder, title=L('SET_TV_ARCHIVE_FOLDER')), selectType=TV_ARCHIVE_FOLDER))
			item_cm.Append(Function(DirectoryItem(selectFolder, title=L('SET_MOVIE_ARCHIVE_FOLDER')), selectType=MOVIE_ARCHIVE_FOLDER))
			dir.Append(DirectoryItem(Route(manageFolders, folder=full_item_path), title=item, thumb=R('folder.png'), contextMenu=item_cm, contextKey=full_item_path, contextArgs={}))
	
	return dir

############################################################################
@route(routeBase + 'selectFolder')
def selectFolder(key=None, selectType=None, sender=None):
  funcName = '[configuration.selectFolder]'
  # The key is the full path to the folder
  # Three types of folders: Download, TV Archive, Movie Archive
  if not key:
    return MessageContainer("Error", "No folder chosen")
  if not type:
    return MessageContainer("Error", "Please choose what you want to do with this folder")
  
  testing = False
  if testing:
    Dict[FSConfigDict] = {}
    Dict.Save()
  
  setDictField(sender=None, query=str(key), theDict=FSConfigDict, key=selectType)
  log(9, funcName, Dict[FSConfigDict])

  return MessageContainer("Saved", "Set folder " + str(getConfigValue(FSConfigDict, str(selectType))) + " as the " + str(selectType))
############################################################################
def configIsValid():
	funcName = "[configuration.configIsValid]"

############################################################################
def setDictField(sender, query, theDict, key):
	funcName = "[configuration.setDictField]"
	log(4, funcName, 'saving', key, 'as', query, 'in', theDict)
	app.cfg.checkDict(theDict)
	thisDict = Dict[theDict]
	thisDict[key] = query
	Dict[theDict] = thisDict
	Dict.Save()
	log(4, funcName, 'saved!')
	configure(None)
	
############################################################################
def getConfigValue(theDict, key):
	funcName = "[configuration.getConfigValue]"
	thisDict = Dict[theDict]
	val = None
	try:
	  val = thisDict[key]
	except:
	  val = ""
	
	return val

############################################################################
def ToggleValue(sender, theDict, key):
	funcName="[configuration.ToggleValue]"
	thisDict = Dict[theDict]
	if getConfigValue(theDict, key)==True:
		setDictField(sender, False, theDict, key)
	else:
		setDictField(sender, True, theDict, key)
