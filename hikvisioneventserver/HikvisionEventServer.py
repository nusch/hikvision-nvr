## python2.7
## Hikvision Event Server
## Tested with Hikvison NVR DS-7608NI-EV2 / 8P
## Written by Ralph Torchia (ralphtorchia1 at gmail dot com)
## Copyrighted 2019
## This code is under the terms of the GPL v3 license.

import ConfigParser
import json
import requests

from hikvisionapi import Client

# Get config settings
class HVServerConfig():
	def __init__(self, configfile):

		self._config = ConfigParser.ConfigParser()
		self._config.read(configfile)
		self.CAMERA = ['0', '1', '2', '3', '4', '5', '6', '7']

		self.IPADDR = self.read_config_var('hikvision', 'ipaddress', 'http://localhost', 'str')
		self.USER = self.read_config_var('hikvision', 'user', 'admin', 'str')
		self.PASS = self.read_config_var('hikvision', 'pass', 'admin', 'str')
		self.HOSTPORT = self.read_config_var('smartthings', 'hostport', 'localhost', 'str')
		self.ACCESSTOKEN = self.read_config_var('smartthings', 'accesstoken', 'accesstoken', 'str')
		self.APPKEY = self.read_config_var('smartthings', 'appkey', 'appkey', 'str')
		
		for i in range(8):
			self.CAMERA[i] = self.read_config_var('cameras', 'cam'+str(i), 'camera '+str(i+1), 'str')

	def read_config_var(self, section, variable, default, type = 'str', quiet = False):
			try:
				if type == 'str':
					return self._config.get(section,variable)
				elif type == 'bool':
					return self._config.getboolean(section,variable)
				elif type == 'int':
					return int(self._config.get(section,variable))
			except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
				self.defaulting(section, variable, default, quiet)
				return default

# Main
while True:
	cfgfile='hikvisionevents.cfg'
	config = HVServerConfig(cfgfile)

	nvr = Client(config.IPADDR, config.USER, config.PASS)
	print 'Monitoring for events from NVR @ http://'+config.IPADDR
	nvrinfo = nvr.System.deviceInfo(method='get')
	print '  Name: ' + nvrinfo['DeviceInfo']['deviceName']
	print '  Serial: ' + nvrinfo['DeviceInfo']['serialNumber']
	print '  Model: ' + nvrinfo['DeviceInfo']['model']
	print '  Firmware: ' + nvrinfo['DeviceInfo']['firmwareVersion']
	
	while True:
		try:

			nvrevent = nvr.Event.notification.alertStream(method='get', type='stream')

			if nvrevent:

				eventchannelID = 'dynChannelID'
				if 'channelID' in nvrevent:
					eventchannelID = 'channelID'
	
				cameranumber = int(nvrevent[0]['EventNotificationAlert'][eventchannelID]) - 1
				if  cameranumber not in range (0,8) :
					cameranumber = 0
			
				body = {
						'eventType': nvrevent[0]['EventNotificationAlert']['eventType'],
						'eventTime': nvrevent[0]['EventNotificationAlert']['dateTime'],
						'cameraName': config.CAMERA[cameranumber],
						'channelName': nvrevent[0]['EventNotificationAlert'][eventchannelID]
						}
		
				headers = {'Content-Type': 'application/json'}
					
				urls = {
						'host': config.HOSTPORT,
						'path': '/api/token/' + config.ACCESSTOKEN + '/smartapps/installations/' + config.APPKEY + '/event',
						'port': '443',
						}

				urlreq = "https://" + urls['host'] + ":" + urls['port'] + urls['path']
				print " Event detected: " + body['eventType'] + " occurred at " + body['eventTime'] + " for camera " + body['cameraName'] + " (channel=" + body['channelName'] + ")"

				stconn = requests.put(urlreq, data=json.dumps(body), headers=headers)
			else:
				print 'Could not open stream to NVR!'
				exit()
	
		except IOError:
			pass
		except KeyboardInterrupt:
			print 'Program exececution halted by user'
			exit()
		except Exception as exception:
			print '--> ', exception
#			pass
