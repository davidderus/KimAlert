# Requirements
import json
import requests

class Push:
	pushURL = 'https://api.pushbullet.com/v2/pushes'
	headers = {'content-type': 'application/json'}
	token = ''
	
	def __init__(self, token, SSL = True):
		self.token = token
		self.SSL = SSL
	title = 'Error from serverChecker'


	# We create the output JSON in a separate method
	def getJSON(self):
		tempJson = {
			'type': self.type,
			'title': self.title,
			'body': self.message
		}

		return json.dumps(tempJson)

	# We send the push
	def send(self, message, title = 'Push', type = 'note'):
		self.type = type
		self.title = title
		self.message = message
		r = requests.post(self.pushURL, data = self.getJSON(), headers = self.headers, auth = (self.token, ''), verify = self.SSL)
		return (True, r.json()) if r.status_code == requests.codes.ok else (False, r.json())