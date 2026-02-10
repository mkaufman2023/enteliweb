"""
enteliWEB REST API wrapper.

Copyright (C) Delta Controls Inc. 2016
"""

# Python built-in modules
import json
import time
import os

# Third-party modules - may require the user to pip install
import requests

# Delta Controls modules
from . import common


class EWEB_API(object):
	"""
	enteliWEB API
	"""

	def __init__(self, session_key, csrf_token_key, base_url):
		self.sessionKey = session_key
		self.csrfTokenKey = csrf_token_key

		self.sessionID = ""
		self.csrfToken = ""

		self.baseURL = base_url

	def Login(self, server, username, password):
		"""
		Perform Login. Store the cookie (session) and CSRF Token

		@param server: The remote enteliWEB server to connect to
		@param username: The username to authenticate
		@param password: The password to authenticate
		@return: True if successful; False otherwise
		"""

		url = "http://" + server + "/enteliweb/api/auth/basiclogin" + '?alt=JSON'
		#print(url)
		try:
			r = requests.get(url, auth=(username, password), headers = {'Content-Type': 'application/json'})
			#print(r)
		except Exception as e:
			print("Login Failed: Server does not exist, or connection timed out")
			return False

		if (r.status_code != requests.codes.ok):
			print("Login Failed: ", r.status_code, r.reason)
			return False

		if (r.text.find('Cannot Connect') > -1):
			print("Login Failed: ", r.text)
			return False

		if (not self.sessionKey in r.cookies.keys()):
			print("Login Failed: ", r.text)
			return False

		self.sessionID = r.cookies[self.sessionKey]
		result = r.json()
		self.csrfToken = result[self.csrfTokenKey]
		print("Login Successful")
		return True


	def do_directory(self, lines):
		if (lines[0] != ""):
			os.chdir( lines[0])

	def CreateObject(self, server, site, device, object_type, instance, name):
		"""
		Create Object

		@param server: The remote enteliWEB server to connect to
		@param site: The site that contains the target device
		@param device: The device address in which to create the object
		@param object_type: The object to create (e.g. AV, TL, etc...)
		@param instance: The object instance
		@param name: The desired object name
		@return: True if successful; False otherwise
		"""

		if (self.sessionID == ""):
			print ("Unable to create object: Not logged in")
			return False

		url = server + self.baseURL + site + '/' + device + '?alt=JSON' + '&' + self.csrfTokenKey + '=' + self.csrfToken

		# json structure for create
		createBody = json.dumps({
			"$base": "Object",
			"object-identifier": {
				"$base": "ObjectIdentifier",
				"value": object_type + ',' + instance
			},
			"object-name": {
				"$base": "String",
				"value": name
			}
		})

		cookies = {
			self.sessionKey: self.sessionID
		}

		headers = {
			'Content-Type': 'application/json'
		}

		r = requests.post(url, data=createBody, cookies=cookies, headers=headers)

		success, code, msg = self._checkError(r)
		print('Creating Object %s: %s %s' % (object_type + ',' + instance, code, msg))
		return r.reason == requests.codes.created


	def CreateObjectM(self, server, site, device, object_type, instance, name, property_value):
		"""
		Create Object

		@param server: The remote enteliWEB server to connect to
		@param site: The site that contains the target device
		@param device: The device address in which to create the object
		@param object_type: The object to create (e.g. AV, TL, etc...)
		@param instance: The object instance
		@param name: The desired object name
		@param property_values: A dictionary containing property names and values
		@return: True if successful; False otherwise
		"""

		if (self.sessionID == ""):
			print ("Unable to create object: Not logged in")
			return False

		url = server + self.baseURL + site + '/' + device + '?alt=JSON' + '&' + self.csrfTokenKey + '=' + self.csrfToken

		valueList = {"$base": "Object"}
		valueList["object-identifier"] = { "$base": "ObjectIdentifier", "value": object_type + ',' + instance }
		valueList["object-name"] =  { "$base": "String", "value": name }

		for property in property_value:
			valueList[property] = { "$base": "String", "value":  property_value[property] }
			
		putBody = json.dumps(valueList)

		cookies = {
			self.sessionKey: self.sessionID
		}

		headers = {
			'Content-Type': 'application/json'
		}

		r = requests.post(url, data=putBody, cookies=cookies, headers=headers)

		success, code, msg = self._checkError(r)
		if (msg == "Created"):
			print ('OK')
		else:
			print('ERROR Creating Object %s: %s' % (object_type + '.' + instance, msg))
		return r.reason == requests.codes.created


	def DeleteObject(self, server, site, device, object_type, instance):
		"""
		Delete Object

		@param server: The remote enteliWEB server to connect to
		@param site: The site that contains the target device
		@param device: The device address in which to delete the object
		@param object_type: The object to delete (e.g. AV, TL, etc...)
		@param instance: The object instance
		@return: True if successful; False otherwise
		"""

		if (self.sessionID == ""):
			print ("Unable to delete object: Not logged in")
			return False

		url = server + self.baseURL + site + '/' + device + '/' + object_type + ',' + instance + '?alt=JSON' + '&' + self.csrfTokenKey + '=' + self.csrfToken

		cookies = {
			self.sessionKey: self.sessionID
		}

		r = requests.delete(url, cookies=cookies)

		success, code, msg = self._checkError(r)

		print('Deleting Object %s: %s %s' % (object_type + ',' + instance, code, msg))
		return r.status_code == requests.codes.non_authoritative_info


	def PutMultiProperty(self, server, site, device, object_type, instance, property_value):
		"""
		Make use of .multi to put multiple properties of an object in one shot

		NOTE: This does not handle sub-properties or array indices; need to extract code from PutProperty to do that

		@param server: The remote enteliWEB server to connect to
		@param site: The site that contains the target device
		@param device: The device address that contains the object being referenced
		@param object_type: The object to reference
		@param instance: The object instance
		@param property_values: A dictionary containing property names and values
		@return: True if successful; False otherwise
		"""

		if (self.sessionID == ""):
			print ("Unable to write properties: Not logged in")
			return False

		url = server + "/enteliweb/api/.multi?alt=json" + '&' + self.csrfTokenKey + '=' + self.csrfToken

		valueList = {
			"$base": "List"
		}

		i = 1
		for property in property_value:
			path = "/.bacnet/" + site + '/' + device + '/' + object_type + ',' + instance + '/'
			path += property
			type = "String"
			value = property_value[property]
			item = {
				"$base": type,
				"via": path,
				"value": value
			}
			valueList[i] = item
			i = i + 1

		struct = {
			"$base": "Struct",
			"values": valueList
		}
		putBody = json.dumps(struct)

		cookies = {
			self.sessionKey: self.sessionID
		}

		headers = {
			'Content-Type': 'application/json'
		}

		r = requests.post(url, data=putBody, cookies=cookies, headers=headers)
		
		success, code, msg = self._checkError(r)
		#print('Modifying Object %s: %s %s' % (object_type + ',' + instance, code, msg))
		if (msg =='OK'):
			print(msg)
		else:
			print ('ERROR WritePropertyMultiple' + device + "." +object_type + instance)
		return r.reason == requests.codes.ok


	def GetMultiProperty(self, server, site, device, object_type, instance, property_value):
		"""
		Make use of .multi to get multiple properties of an object in one shot

		NOTE: This does not handle sub-properties or array indices; need to extract code from PutProperty to do that

		@param server: The remote enteliWEB server to connect to
		@param site: The site that contains the target device
		@param device: The device address that contains the object being referenced
		@param object_type: The object to reference
		@param instance: The object instance
		@param property_values: A dictionary containing property names and values
		@return: A dictionary of properties and values
		"""

		if (self.sessionID == ""):
			print ("Unable to get properties: Not logged in")
			return {}

		url = server + "/enteliweb/api/.multi?alt=json" + '&' + self.csrfTokenKey + '=' + self.csrfToken

		valueList = {
			"$base": "List"
		}

		i = 1
		for property in property_value:
			path = "/.bacnet/" + site + '/' + device + '/' + object_type + ',' + instance + '/'
			path += property
			type = "Any"
			item = {
				"$base": type,
				"via": path
			}
			valueList[i] = item
			i = i + 1

		struct = {
			"$base": "Struct",
			"lifetime": {
				"$base": "Unsigned",
				"value": "0"
			},
			"values" : valueList
		}

		putBody = json.dumps(struct)

		cookies = {
			self.sessionKey: self.sessionID
		}

		headers = {
			'Content-Type': 'application/json'
		}

		r = requests.post(url, data=putBody, cookies=cookies, headers=headers)

		success, code, msg = self._checkError(r)
		if (success != True):
			print("Error: %s %s" % (code, msg))
			return {}

		result = r.json()
		values = result['values']
		valueList = {}
		for key in values:
			if ('via' in values[key]):
				path = values[key]['via']
				property = path[path.rfind('/') + 1:]
				
				if ('value' in values[key]):
					value = str(values[key]['value'])
				else:
					value = ""
				
				valueList[property] = value

		return valueList


	def PutProperty(self, server, site, device, object_type, instance, property, type, value):
		"""
		PutProperty - Perform an simple put property single

		@param server: The remote enteliWEB server to connect to
		@param site: The site that contains the target device
		@param device: The device address that contains the object being referenced
		@param object_type: The object to reference
		@param instance: The object instance
		@param property: The property to write
		@param type: The type of the property
		@param value: The value to write
		@return: True if the write was successful; False otherwise
		"""

		if (self.sessionID == ""):
			print ("Unable to write property: Not logged in")
			return False

		# Detect sub-property and array index
		property = property.replace('[', '.')
		property = property.replace(']', '')
		property = property.replace('.', '/')

		url = server + self.baseURL + site + '/' + device + '/' + object_type + ',' + instance + '/' + property
		url += '?alt=JSON' + '&' + self.csrfTokenKey + '=' + self.csrfToken

		putBody = json.dumps({
			"$base": type,
			"value": value
		})

		cookies = {
			self.sessionKey: self.sessionID
		}

		headers = {
			'Content-Type': 'application/json'
		}

		r = requests.put(url, data=putBody, cookies=cookies, headers=headers)

		success, code, msg = self._checkError(r)

		print('Put Property %s.%s = %s: %s %s' % (object_type + ',' + instance, property, value, code, msg))
		return r.status_code == requests.codes.ok


	def GetSites(self, server):
		"""
		List all sites

		@param server: The remote enteliWEB server to connect to
		@return: A list of sites; an empty list if there are no sites or an error occurred
		"""

		if (self.sessionID == ""):
			print ("Unable to get sites: Not logged in")
			return []

		sites = []

		url = server + self.baseURL + '?alt=JSON' + '&' + self.csrfTokenKey + '=' + self.csrfToken

		cookies = {
			self.sessionKey: self.sessionID
		}

		headers = {
			'Content-Type': 'application/json'
		}

		r = requests.get(url, cookies=cookies, headers=headers)

		success, code, msg = self._checkError(r)
		if (success != True):
			print("Error: %s %s" % (code, msg))
			return []

		result = r.json()
		for key in sorted(result):
			if ("nodeType" in result[key] and result[key]["nodeType"] == "NETWORK"):
				sites.append(key)

		return sites


	def GetDevices(self, server, site):
		"""
		List all devices from the specified site

		@param server: The remote enteliWEB server to connect to
		@param site: The site in which to get a list of devices
		@return: A list of devices; an empty list if there are no devices or an error occurred
		"""

		if (self.sessionID == ""):
			print ("Unable to get devices: Not logged in")
			return []

		devices = []

		url = server + self.baseURL + site + '?alt=JSON' + '&' + self.csrfTokenKey + '=' + self.csrfToken

		cookies = {
			self.sessionKey: self.sessionID
		}

		headers = {
			'Content-Type': 'application/json'
		}

		r = requests.get(url, cookies=cookies, headers=headers)

		if (r.status_code != requests.codes.ok):
			print("Error: %s %s" % (r.status_code, r.reason))
			return []

		result = r.json()
		for key in sorted(result, key=common.custom_key):
			if ("nodeType" in result[key] and result[key]["nodeType"] == "DEVICE"):
				devices.append("%s - %s" % (key, result[key]["displayName"]))

		return devices

	def SaveDB(self, server, site, device, sPath):
		"""
		save controller database to file

		@param server: The remote enteliWEB server to connect to
		@param site: The site in which the device is
		@param device: The device to save
		@return: a backup of the device; nothing when there are no devices or an error occurred
		"""

		if (self.sessionID == ""):
			print ("Unable to get devices: Not logged in")
			return []

		url = server + "/enteliweb/wsbac/sendstartsavedatabasecurl"

		cookies = {
			self.sessionKey: self.sessionID
		}

		data = {
			"deviceRef" : "//" + site  + "/" + device + ".DEV" + device ,
			self.csrfTokenKey :  self.csrfToken
			}
		r = requests.post(url, cookies=cookies, data=data)
		"""
		success, code, msg = self._checkError(r)
		print('Start Save Database %s = %s %s %s' % (device, code, msg, r.content))
		"""
		i = 1
		response = r.json()  
		if (response["success"]):
			#filepath = 'C:\Users\Public\Documents' 
			filepath = response["filepath"]
			filename = response["filename"]

			url = server + "/enteliweb/wsbac/checksavedatabase"
			data = {
				"filepath" :  filepath,
				"filename" :  filename,
				self.csrfTokenKey :  self.csrfToken
				}

			while i < 100:
				r = requests.post(url, cookies=cookies, data=data)
				#success, code, msg = self._checkError(r)
				#print('Check Save Database %s = %s %s %s' % (device, code, msg, r.content))

				response = r.json()
				if response["status"] == 1:
					break
				i += 1
				time.sleep(5)

			if response["status"] == 1:
				url = server + "/enteliweb/wsbac/savedatabasefile"
				data = {
					"saveDBToken" : filepath + "/" + filename,
					"deviceRef" : "//" + site  + "/" + device + ".DEV" + device ,
					self.csrfTokenKey :  self.csrfToken
					}
				#print(data)
				r = requests.post(url, cookies=cookies, data=data)
				
				#response = r.json()
				# make file
				if bool(sPath):
					currdir = os.getcwd()
					os.chdir( sPath)
				File = open( filename + ".zdd", "wb")
				# write to file
				File.write(r.content)
				File.close()
				if bool(sPath):
					os.chdir( currdir)
				print ("OK")
			else :
				print ('ERROR saveDB DEV' + device)
		else :
			print ('ERROR saveDB DEV' + device)
		return

	def LoadPG(self, server, site, device, object, file):
		"""
		load pg  with text file 

		@param server: The remote enteliWEB server to connect to
		@param site: The site in which the device is
		@param device: The device to save
		@param object: The program to save the text file in
		@param file: the text file
		@return: succes
		"""

		if (self.sessionID == ""):
			print ("Unable to get devices: Not logged in")
			return []

		url = server + "/enteliweb/wsbac/saveprogram" 

		cookies = {
			self.sessionKey: self.sessionID
		}
		
		#load File in object
		f = open(file, "r")		
		strPgText = f.read()
		f.close()
		data = {
			"Name" : "Test",
			"OldProgramText" : "",
			"IgnoreErrors" : "true",
			"PGObjRef" : '//' + site  + '/' + device + '.' + object  ,
			"ProgramText" : strPgText,
			self.csrfTokenKey : self.csrfToken }
		#print (data)
		r = requests.post(url, cookies=cookies, data=data)
		response = r.text
		if (response.find('OK') != -1):		   
			print ("OK")
		else :
			print ('ERROR Load textfile in '+ object)
		return 

	def LoadDB(self, server, site, device, file):
		"""
		load controller  with file database 

		@param server: The remote enteliWEB server to connect to
		@param site: The site in which the device is
		@param device: The device to load database
		@param file: file to load in controller		
		@return: succes
		"""

		if (self.sessionID == ""):
			print ("Unable to get devices: Not logged in")
			return []

		url = server + "/enteliweb/wsbac/loaddevicedatabasefile" 

		cookies = {
			self.sessionKey: self.sessionID
		}
		
		#load File in object
		f = open(file, "rb")		
		datafile = {"loadDBFromFile" : f}
		#print(datafile)
		data = {
			"password" : "",
			"deviceRef" : '"//' + site  + '/' + device + '.DEV' + device+ '"' ,
			self.csrfTokenKey : self.csrfToken }
		#print (data)
		r = requests.post(url, cookies=cookies, files=datafile, data=data)
		success, code, msg = self._checkError(r)
		response = r.json()
		#print('load Database DEV%s = %s %s %s' % (device, code, msg ,response))
		
		if (response['success']):		   
			url = server + "/enteliweb/wsbac/waitfordeviceonline/" 
			data = {
				"deviceRef" : '["//' + site  + '/' + device + '.DEV' + device+ '"]' ,
				self.csrfTokenKey :  self.csrfToken
				}

			r = requests.post(url, cookies=cookies, data=data)
			#success, code, msg = self._checkError(r)
			#print('Check Device online %s = %s %s' % (device, code, msg))
			#response = r.json()	   
			#print (response)
			print (msg)
		else :
			print ('ERROR Load file in DEV'+ device)
		return 
 
	def SaveObj(self, server, site, device,line):
		"""
		save BACnet Object(s) to file

		@param server: The remote enteliWEB server to connect to
		@param site: The site in which the device is
		@param device: The device to save
		@param line: lijst met BACnet objects example ai12;av132
		@return: a file with BACnet object(s); nothing when there are no devices or an error occurred
		"""
		objects = line.split(";")
		if (self.sessionID == ""):
			print ("Unable to get devices: Not logged in")
			return []

		url = server + "/enteliweb/wsbac/backupobject" 

		cookies = {
			self.sessionKey: self.sessionID
		}

		i = 1
		for object in objects:
			if (i == 1):
				ref = '"'+ "//" + site  + "/" + device + "." + object +'"'
				i += 1
			else:
				ref = ref +',"'+ "//" + site  + "/" + device + "." + object +'"'
		
		data = {
			"saveObjectRef" : "[" + ref + "]",
			self.csrfTokenKey :  self.csrfToken
			}
		r = requests.post(url, cookies=cookies, data=data)

		#success, code, msg = self._checkError(r)
		#print('Backup Object(s) %s = %s %s' % (device, code, msg))

		response = r.json()
		if (response['success']):
			file = response["file"] 
			feedback = response["result"] 

			url = server + "/enteliweb/wsbac/saveobjectfile" 
			data = {
				"file" : file,
				"feedback" : feedback,
				self.csrfTokenKey :  self.csrfToken
				}

			r = requests.post(url, cookies=cookies, data=data)
			# make file
			if (len(objects) == 1):
				filename =  site + "_" + device + "_" + objects[0] + ".zob"
			else:
				filename =  site + "_" + device + "_" + objects[0] + ".zip"
			
			File = open( filename, "wb")
			# write to file
			File.write(r.content)
			File.close()
			print (r.status_code)
		else :
			print("ERROR Save Object DEV" + device + " " + line)
		return 

	def LoadObj(self, server, site, device, objectinstance, name, file):
		"""
		load object from file to controller
		
		@param server: The remote enteliWEB server to connect to
		@param site: The site in which the device is
		@param device: The device to save
		@param object: BACnet objectinstance to load the file
		@param name: new object name 
		@param file: file to load 
		@return: ok or error
		"""
		if (self.sessionID == ""):
			print ("Unable to get devices: Not logged in")
			return []
		url = server + "/enteliweb/wsbac/uploadobjectfile"
		
		cookies = {self.sessionKey: self.sessionID}
		
		f = open( file, "rb")		
		# datafile = { "objectFile-button" : f, "filetype" : "application/octet-stream"}
		datafile = { "objectFile-button" : f}
		#print (file)
		
		data = { 
			"deviceRef" : '["//' + site  + '/' + device + '.DEV' + device+ '"]' ,
			self.csrfTokenKey : self.csrfToken }
		
		r = requests.post(url, cookies=cookies, files=datafile, data=data)

		response = r.json() 
		if (response['success']):

			eWebfile = response["objInfo"][0]["file"]
			eWebfile1 = eWebfile.replace("\\",r"\\")
			
			objtype = response["objInfo"][0]["type"]
			
			objinstance = response["objInfo"][0]["instance"]
			
			objname = response["objInfo"][0]["objName"]
			
			url = server + "/enteliweb/wsbac/restoreobject"

			data = {
				"objList":'[{"name":"' + name + '","ref":"//' + site + '/' + device + '.' + objtype + objinstance + '",' +
				'"file":"' + eWebfile1 +'","instance":'+ objectinstance + '}]', 
				"skipUpdate":"true",
				"startInstance":"",
				"devices":'["//' + site  + '/' + device + '.DEV' + device + '"]',
				"esignature_password":"",
				self.csrfTokenKey:self.csrfToken }

			r = requests.post(url, cookies=cookies, data=data)
			
			response = r.json()	   
			print (response[0]['status'])
		else :
			print ("ERROR Load object failed to DEV" + device + ' ' + objtype + objinstance )
		return 

	def CopyObject(self, server, site, device, object_type, instance, toInstance, objectname):
		"""
		copy Object

		@param server: The remote enteliWEB server to connect to
		@param site: The site that contains the target device
		@param device: The device address in which to create the object
		@param object_type: The object to create (e.g. AV, TL, etc...)
		@param instance: The object instance
		@param instance: To Instance
		@param objectname: The desired object name
		@return: True if successful; False otherwise
		"""

		if (self.sessionID == ""):
			print ("Unable to create object: Not logged in")
			return False

		cookies = {
			self.sessionKey: self.sessionID
		}

		url = server + "/enteliweb/wsbac/getsuggestedpastedata"
		data = {
			"refs" : "[" + '"' + "//" + site  + "/" + device + "." + "EV" + instance + '"' +"]",
			"devices" : "[" + '"' + "//" + site  + "/" + device + ".DEV" + device + '"' + "]",
			"names" : "[" + '"' + "" + '"' + "]" ,
			self.csrfTokenKey :  self.csrfToken
			}
		
		r = requests.post(url, cookies=cookies, data=data)
		#success, code, msg = self._checkError(r)
		#print('Prepare Copying Object %s: %s %s' % (object_type + ',' + instance, code, msg))
		
		url = server + "/enteliweb/wsbac/createpasteobjecttask"
		data = { self.csrfTokenKey :  self.csrfToken }
		
		r = requests.post(url, cookies=cookies, data=data)
		#success, code, msg = self._checkError(r)
		#print('Create task Copying Object %s: %s %s' % (object_type + ',' + instance, code, msg))
		response = r.json()	   
		taskid = response["taskid"] 

		url = server + "/enteliweb/wsbac/pasteobject"
		dataref = {
			"ref" : '"' + "//" + site  + "/" + device + "." + "EV" + instance + '"',
			"name": objectname ,
			"instance": toInstance
			}
		
		data = {
			"type" : "local",
			"data" : '[{'+ 
					 '"ref"' + ':' + '"' + '//'+ site  + '/' + device + '.' + 'EV' + instance + '",' +
			'"name" : "' + objectname + '",'
			'"instance": ' + toInstance +"}]",
			"target" : "[" + '"' + "//" + site  + "/" + device + ".DEV" + device + '"' +"]",
			"startInstance" : "",
			"ignoreSpecialAlgorithm" : "true",
			"taskID" : taskid,
			self.csrfTokenKey :  self.csrfToken
			}
		#print(data)
		
		r = requests.post(url, cookies=cookies, data=data)

		url = server + "/enteliweb/wstaskqueue/getcopypastetaskprogress" 
		i =1
		while i < 10:
			r = requests.get(url, cookies=cookies)
			response = r.json()
			
			for each in response:
				#print (each['taskID'], each['progress'])
				if each['taskID'] == taskid and each['progress'] == 100 :
					i = 10
			i += 1
			if i < 10:
				time.sleep(5)
			
		#success, code, msg = self._checkError(r)
		#print('Check progress %s = %s %s %s' % (device, code, msg, r.content))

		url = server + "/enteliweb/wstaskqueue/getmergedtasktargetparamdata"
		data = { 
			"taskID" : taskid,
			self.csrfTokenKey :  self.csrfToken 
			}
		
		r = requests.post(url, cookies=cookies, data=data)
		success, code, msg = self._checkError(r)
		#print('mergedtask %s: %s %s' % (object_type + ',' + instance, code, msg))
		response = r.json()   
		print('copy %s ' % (response))	
		return r.reason == requests.codes.created

	def GetObjects(self, server, site, device):
		"""
		List all objects from the specified device on the specified site

		@param server: The remote enteliWEB server to connect to
		@param site: The target site
		@param device: The device address in which to get a list of objects
		@return: A list of objects; an empty list if there are no objects or an error occurred
		"""

		if (self.sessionID == ""):
			print ("Unable to get devices: Not logged in")
			return []

		objects = []

		url = server + self.baseURL + site + '/' + device + '/' + '?alt=JSON' + '&' + self.csrfTokenKey + '=' + self.csrfToken

		cookies = {
			self.sessionKey: self.sessionID
		}

		headers = {
			'Content-Type': 'application/json'
		}

		r = requests.get(url, cookies=cookies, headers=headers)

		if (r.status_code != requests.codes.ok):
			print("Error: %s %s" % (r.status_code, r.reason))
			return []

		result = r.json()
		for key in sorted(result):
			if ("$base" in result[key] and result[key]["$base"] == "Object"):
				objects.append(key)

		return objects


	def _checkError(self, response):
		"""
		Parses a response for a successful response code

		@param response: A python HTTP response object
		@return: A tuple containing the success status (True / False), response code and response reason
		"""

		if (response.status_code == requests.codes.ok):
			result = response.json()
		else:
			result = {}

		if ("error" in result and result["error"] != "-1"):
			code = result["error"]
			msg	= result["errorText"]
		else:
			if (response.status_code == requests.codes.non_authoritative_info):
				code = str(requests.codes.ok)
				msg = "OK"
			else:
				code = str(response.status_code)
				msg	= response.reason
		success = (code == str(response.status_code))
		return (success, code, msg)


	def _findAbbr(self, bacnet_object_name):
		"""
		Resolves a BACnet object name (i.e. 'analog-input', 'trend-log', etc...) to its corresponding abbreviation

		@param bacnet_object_name: The fully-specified BACnet object name
		@return: The object abbreviation if found; an empty string otherwise
		"""

		for object_abbreviation, mapped_bacnet_object_name in common.OBJECT_NAME_MAP.items():
			if bacnet_object_name == mapped_bacnet_object_name:
				return object_abbreviation
		return ""


