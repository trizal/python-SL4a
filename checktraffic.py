"""Retrive traffic report """

__author__ = 'Tubagus Rizal, trizal@gmx.com'
__copyright__ = 'Copyright (c) 2009, Bizzet Ltd.'


import urllib
import sys, logging, json
import android
import math


LOGGING_ACTIVE = 0
LOGFILE = '/sdcard/sl4a/checkmway.py.log'

RADIUS_IN_MILES = 3960
MAXIMUM_DISTANCE = 25

# YQL related constants
TRAFFIC_INFO = 'http://hatrafficinfo.dft.gov.uk/feeds/rss/UnplannedEvents.xml'
YQL_BASE = 'http://query.yahooapis.com/v1/public/yql?q=select * from rss where url='
YQL_SWITCHES = '&format=json&callback='
YQL_TRAFFIC = 'http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20rss%20where%20url%3D\'http%3A%2F%2Fhatrafficinfo.dft.gov.uk%2Ffeeds%2Frss%2FUnplannedEvents.xml\'&format=json&callback='




class StreamToLogger(object):
	"""
	Fake file-like stream object that redirects writes to a logger instance.
	A very useful class indeed
	requires import sys  & logging
	"""
	def __init__(self, logger, log_level=logging.INFO):
		self.logger = logger
		self.log_level = log_level
		self.linebuf = ''

	def write(self, buf):
		for line in buf.rstrip().splitlines():
			self.logger.log(self.log_level, line.rstrip())

	logging.basicConfig(
		level = logging.DEBUG,
		format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s',
		filename = LOGFILE,
		filemode = 'a')
		
def distanceHaversine(lat1, lon1, lat2, lon2):
		# calculate the distance between two GPS coordinates
		# don't really care with the earth curvature as the distance
		# between the two points is miniscule compared to earth's circumvent
		# unit is in miles
		
		lat1 = float(lat1)
		lat2 = float(lat2)
		lon1 = float(lon1)
		lon2 = float(lon2)
		distance = 0
		
		if ((lat1 != lat2) and (lon1 != lon2) and (lat1 != 0) and (lat2 !=0)):
			dlat = math.radians(lat2 - lat1)
			dlon = math.radians(lon2 - lon1)
			aa = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
			* math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
			c = 2 * math.atan2(math.sqrt(aa), math.sqrt(1-aa))
			distance = RADIUS_IN_MILES * c
		
		# logging.debug('distance is:' + str(distance) + ' miles')
		return float(distance)

def main():
	if LOGGING_ACTIVE :
		#redirect STDOUT into logfile
		stdout_logger = logging.getLogger('STDOUT')
		sl = StreamToLogger(stdout_logger, logging.INFO)
		sys.stdout = sl
		
		#redirect STDERR into logfile
		stderr_logger = logging.getLogger('STDERR')
		sl = StreamToLogger(stderr_logger, logging.ERROR)
		sys.stderr = sl
		
		#download traffic info
		haTrafficInfo = None
		
	try:
		haTrafficInfo = json.loads(urllib.urlopen(YQL_TRAFFIC).read())
	except:
		print 'Not able to get traffic info. Exiting'
		sys.exit()
		
	droid = android.Android()
	location = droid.getLastKnownLocation().result
	if location['gps'] is not None:
		location = location['gps']
	else:
		location = location['network']
	
	#count how many incident in the file
	trafficIncidentCount = haTrafficInfo['query']['count']
	trafficIncidents = haTrafficInfo['query']['results']['item']
	
	if LOGGING_ACTIVE :
		print str(location)
		print 'number of incident: ' + str(len(trafficIncidents))


	for incident in trafficIncidents:
		distance = distanceHaversine(location['latitude'],location['longitude'],incident['latitude'],incident['longitude'])
		if distance <= MAXIMUM_DISTANCE:
			trafficDescription = ['Category: ' + incident['category'][1]]
			trafficDescription.append('Radius: %d.2' % distance + ' miles')
			trafficDescription.append(incident['description'])
			droid.dialogCreateAlert(incident['title'],'\n\n'.join(trafficDescription))
			droid.dialogSetPositiveButtonText('OK')
			droid.dialogShow()
			response=droid.dialogGetResponse().result
			droid.dialogDismiss()



if __name__ == "__main__":
	main()