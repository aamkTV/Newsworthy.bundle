from common import *

class nntpObj(object):
	def __init__(self):
		if nntpConfigDict in Dict:
			pass
		else:
			Dict[nntpConfigDict] = {}
	
	@property
	def nntpUsername(self):
		return getConfigValue(theDict=nntpConfigDict, key='nntpUsername')

	@property
	def nntpPassword(self):
		return getConfigValue(theDict=nntpConfigDict, key='nntpPassword')

	@property	
	def nntpHost(self):
		return getConfigValue(theDict=nntpConfigDict, key='nntpHost')
	
	@property
	def nntpPort(self):
		return getConfigValue(theDict=nntpConfigDict, key='nntpPort')

	@property
	def nntpSSL(self):
		return getConfigValue(theDict=nntpConfigDict, key='nntpSSL')
		
	@property
	def nntpConnections(self):
		return getConfigValue(theDict=nntpConfigDict, key='nntpConnections')

@route('/video/newzworthy/configure')
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
	
	nntp = nntpObj()
	
	cm = ContextMenu(includeStandardItems=False)
	cm.Append(Function(DirectoryItem(StupidUselessFunction, title="N/A")))
	dir = MediaContainer(contextMenu=cm, replaceParent=False, noHistory=False, noCache=True)
	
	###########################
	# NZB CONFIGURATION SECTION
	# Present the user with the options to configure their nzb service info
	
	###########################
	# NZBMatrix Configs
	if Prefs['NZBService'] == 'NZBMatrix':
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
	if Prefs['NZBService'] == 'Newzbin':
		dir.Append(Function(InputDirectoryItem(setDictField, title=("Newzbin Username: " + getConfigValue(theDict=nzbConfigDict, key='newzbinUsername')), prompt=("Set Newzbin Username"), contextKey="a", contextArgs={}), theDict=nzbConfigDict, key='newzbinUsername'))
		if len(getConfigValue(theDict=nzbConfigDict, key='newzbinPassword'))>=1:
			dir.Append(Function(InputDirectoryItem(setDictField, title=("Newzbin Password: ******"), prompt=("Set Newzbin Password"), contextKey="a", contextArgs={}), theDict=nzbConfigDict, key='newzbinPassword'))
		else:
			dir.Append(Function(InputDirectoryItem(setDictField, title=("Newzbin Password: <Not Set>"), prompt=("Set Newzbin Password"), contextKey="a", contextArgs={}), theDict=nzbConfigDict, key='newzbinPassword'))
			
	##########################################
	# NNTP (News Server) CONFIGURATION SECTION
	# Present the user with the options to configure their news servers
	dir.Append(Function(InputDirectoryItem(setDictField, title=("News Server: " + nntp.nntpHost), prompt=L("Set News Server Host"), contextKey="a", contextArgs={}), theDict=nntpConfigDict, key='nntpHost'))
	dir.Append(Function(InputDirectoryItem(setDictField, title=("News Server Port: " + nntp.nntpPort), prompt=L("Set News Server Port"), contextKey="a", contextArgs={}), theDict=nntpConfigDict, key='nntpPort'))
	dir.Append(Function(DirectoryItem(ToggleValue, title=("News Server SSL? " + str(nntp.nntpSSL)), contextKey="a", contextArgs={}), theDict=nntpConfigDict, key='nntpSSL'))
	dir.Append(Function(InputDirectoryItem(setDictField, title=("News Server Username: " + nntp.nntpUsername), prompt=L('Set News Server Username'), contextKey="a", contextArgs={}), theDict=nntpConfigDict, key='nntpUsername'))
	try:
		if len(getConfigValue(theDict=nntpConfigDict, key='nntpPassword'))>=1:
			dir.Append(Function(InputDirectoryItem(setDictField, title=("News Server Password: ******"), prompt=L('Set News Server Password'), contextKey="a", contextArgs={}), theDict=nntpConfigDict, key='nntpPassword'))
		else:
			dir.Append(Function(InputDirectoryItem(setDictField, title=("News Server Password: <Not Set>"), prompt=L('Set News Server Password'), contextKey="a", contextArgs={}), theDict=nntpConfigDict, key='nntpPassword'))
	except:
		dir.Append(Function(InputDirectoryItem(setDictField, title=("News Server Password: <Not Set>"), prompt=L('Set News Server Password'), contextKey="a", contextArgs={}), theDict=nntpConfigDict, key='nntpPassword'))
	dir.Append(Function(InputDirectoryItem(setDictField, title=("Number of NNTP Connections: " + nntp.nntpConnections), prompt="Set the number of NNTP connections to use", contextKey="a", contextArgs={}), theDict=nntpConfigDict, key='nntpConnections'))
	 
	 ##################################
	 # Filesystem configuration section
	 # Ask the user where they want to save the files
	#dir.Append(Function(InputDirectoryItem(setDictField, title=("Download To (i.e. Temp): " + getConfigValue(theDict=FSConfigDict, key='downloadDir')), prompt="Set the download directory", contextKey="a", contextArgs={}), theDict=FSConfigDict, key='downloadDir'))
	#dir.Append(Function(InputDirectoryItem(setDictField, title=("Archive To: " + getConfigValue(theDict=FSConfigDict, key='archiveDir')), prompt="Set the download archive directory", contextKey="a", contextArgs={}), theDict=FSConfigDict, key='archiveDir'))
	#dir.Append(Function(DirectoryItem(ToggleValue, title=("Auto Archive? " + str(getConfigValue(theDict=FSConfigDict, key='autoArchive'))), prompt="Auto Archive Downloads?", contextKey="a", contextArgs={}), theDict=FSConfigDict, key='autoArchive'))
	 
	return dir
	
############################################################################
def configIsValid():
	funcName = "[configuration.configIsValid]"

############################################################################
def setDictField(sender, query, theDict, key):
	funcName = "[configuration.setDictField]"
	log(4, funcName, 'saving', key, 'as', query)
	thisDict = Dict[theDict]
	thisDict[key] = query
	Dict[theDict] = thisDict
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