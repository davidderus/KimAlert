#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime, time
import os.path

import requests
from lxml.html import parse

from pprint import pprint

from threading import Thread
from Queue import Queue

from push import Push

import argparse

class KimAlert():
	pageLink = 'http://www.kimsufi.com/fr/index.xml'
	listLink = 'https://ws.ovh.com/dedicated/r2/ws.dispatcher/getAvailability2'
	availabilityLink = 'https://ws.ovh.com/dedicated/r2/ws.dispatcher/getElapsedTimeSinceLastDelivery?params={"gamme":"%s"}'
	zones = {'France':['gra', 'rbx', 'sbg'], 'Canada':['bhs']}

	def __init__(self):
		startTime = time.time()
		# Init Queue
		self.q = Queue(200 * 2)
		for i in range(200):
			t = Thread(target=self.startQueue)
			t.daemon = True
			t.start()
		# Arguments parser
		parser = argparse.ArgumentParser(description = 'A simple Kimsufi Seeker')
		parser.add_argument('-k', help = 'Kimsufi names (single or list, comma separated)', metavar="KS-0")
		parser.add_argument('-t', help = 'Pushbullet Token')
		args = parser.parse_args()
		# Defining globals
		self.pToken = args.t
		# Starting script
		print '== Starting script =='
		ks = self.retriever()
		if args.k:
			print '== Notifying availabilities =='
			self.ksNames = args.k.split(',')
			self.isAvailable(ks)
		else:
			pprint(ks)
		print '== Script took %.2fs ==' % (time.time() - startTime,)

	def startQueue(self):
		while True:
			try:
				entry = self.q.get()
				self.handleEntry(entry)
				self.q.task_done()
			except Exception, e:
				print 'Error', e

	def retriever(self):
		# Retrieving actual KS list
		self.ks = self.getTable()
		# Getting Current Status of All KS
		self.stats = self.parseJSON()
		# Merging the result and returning the result
		return self.mergeResults()

	# We parse Kimsufi website to get all servers references
	def getTable(self):
		page = parse(self.pageLink).getroot()
		table = {}
		for tr in page.cssselect('.homepage-table tr.zone-dedicated-availability'):
			ref = tr.get('data-ref')
			td = tr.cssselect('td')
			name = td[0].text_content()
			price = td[9].find('span').text_content()
			link = 'https://www.kimsufi.com/fr/commande/kimsufi.xml?reference=%s&quantity=1' % ref
			table[ref] = {'name' : name, 'link': link, 'price': price, 'ref': ref}
		return table

	# Getting JSON feed containing availabilities
	def getJSON(self):
		page = requests.get(self.listLink)
		if not page.status_code is 200:
			print 'Error while getting the feed'
			exit(0)
		json = page.json()
		return json

	# Foreach entry in server JSON, we make some operations 
	def parseJSON(self):
		self.result = {}
		json = self.getJSON()
		json = json['answer']['availability']
		for entry in json:
			# Will use handleEntry to process this entry
			self.q.put(entry)
		self.q.join()
		return self.result

	# Verifying the availability, if not getting last time
	def handleEntry(self, entry):
		zones = entry['zones']
		zonesResult = {'available':[], 'isCanada':[]}
		for zone in zones:
			if zone['availability'] == 'unavailable' or zone['availability'] == 'unknown':
				zonesResult['available'].append(False)
			else:
				zonesResult['available'].append(True)

		if True in zonesResult['available']:
			zonesResult = True
		else:
			zonesResult = False
		self.result[entry['reference']] = {'available':zonesResult}
		if not zonesResult:
			self.result[entry['reference']]['lastTime'] = self.getLastTime(entry['reference'])

	# Getting last time a server was available to sell
	def getLastTime(self, ref):
		page = requests.get(self.availabilityLink % ref)
		if not page.status_code is 200:
			print 'Error while getting the availability of %s' % (ref,)
			return 0
		json = page.json()['answer']
		if not json:
			return 0
		time = datetime.datetime.fromtimestamp(int(json)).strftime('%H:%M:%S')
		return str(time)

	# Merging servers with servers availabilities
	def mergeResults(self):
		ksCopy = self.ks
		for key in ksCopy.keys():
			ksCopy[key] = dict(ksCopy[key].items() + self.stats[key].items())
		resultKs = {}
		for (ref, content) in ksCopy.items():
			resultKs[content['name']] = content
		return resultKs

	# Testing availability
	def isAvailable(self, ksList):
		messages = []
		for ksName in self.ksNames:
			if not ksList.get(ksName, None):
				print '%s does not exist' % ksName
				continue
			ksData = ksList[ksName]
			if ksData['available'] is True:
				messages.append('%s is available for %s€ : %s\r\n' % (ksName, ksData['price'], ksData['link']))
			elif not self.pToken:
				messages.append('%s is unavailable' % ksName)
		if len(messages) == 0:
			return
		if self.pToken:
			push = Push(self.pToken)
			push.send('\r\n'.join(messages), 'KimAlert Notification')
			print 'Push sent'
		else:
			print '\r\n'.join(messages)

# Let's start!
KimAlert()