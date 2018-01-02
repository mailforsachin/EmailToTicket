from datetime import timedelta
from exchangelib import DELEGATE, IMPERSONATION, Account, Credentials, ServiceAccount, \
    EWSDateTime, EWSTimeZone, Configuration, NTLM, CalendarItem, Message, \
    Mailbox, Attendee, Q, ExtendedProperty, FileAttachment, ItemAttachment, \
    Body, HTMLBody, Build, Version
import codecs
import numpy as np
import spacy
import helper as fx
import json
import uuid, pymongo, requests
from azure.servicebus import ServiceBusService, Message, Queue
from hashlib import md5

print "Loading Spacy"
pos = spacy.load('en')
print "spacey loaded"
credentials = Credentials(username='127334@nttdata.com', password='$')

print "connecting to exchange"
account = Account(primary_smtp_address='127334@nttdata.com', credentials=credentials,autodiscover=True, access_type=DELEGATE)
print "connected"


unread  = account.inbox.filter(is_read=True).only('sender','to_recipients','cc_recipients','subject','datetime_received','text_body','body').order_by('-datetime_received')[:1]
#unread  = account.inbox.filter(is_read=False).order_by('-datetime_received')[:1]

emails = [i for i in unread]


#LUIS
luis_url = "https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/b922584b-1136-4b37-969e-9f0df9cb4579?subscription-key=62ea92a6dad241628c1489c0333d166f&verbose=true&timezoneOffset=330&q="

#MongoDB Connection
client = pymongo.MongoClient('mongodb://serivice-desk-store:pMzmGDeCcbMZEJ7hVirY9YEA7NMm6abpGF6oNz32D6MNTqsmdqzvdg3MLVw80eMlztxPP03vxsKxtatgPOiCFg==@serivice-desk-store.documents.azure.com:10255/?ssl=true&replicaSet=globaldb')
db = client.hilton
sdmails  = db.emails

#Azure Service Bus Connection

for email in emails:
	try:
		mail = {}
		mail['from'] = fx.getContact(email.sender)
		mail['to'] = fx.getContacts(email.to_recipients)
		if email.cc_recipients:
			mail['cc'] = fx.getContacts(email.cc_recipients) 
		mail['subject'] = email.subject
		msgs = fx.process(email.text_body)
		uniqueMessage = msgs[0]
		mailtrail = msgs[1:]
		mail['message'] = uniqueMessage
		jmsg = [' '.join for i in msgs]

		allemails = []
		for utt in jmsg:
			url = luis_url + str(utt)
			res = requests.get(url)
			if res.status_code == 200:
				vals = res.json()
				score = vals['topScoringIntent']['score']
				intent = vals['topScoringIntent']['intent']
				m  = {'intent':intent, 'message':utt}
				allemails.append(m)

		mail[emails] = allemails

		print allemails

		utt = ''.join(uniqueMessage)
		url = luis_url + str(utt)
		res = requests.get(url)
		if res.status_code == 200:
			vals = res.json()
			mail['intent'] = vals

		id = sdmails.insert_one(mail).inserted_id
	except Exception,e:
		print email.subject
		print str(e)
		pass

'''
for line in uniqueMessage:
			url = luis_url + str(line)
			res = requests.get(url)
			if res.status_code == 200:
				vals = res.json()
				score = vals['topScoringIntent']['score']
				intent = vals['topScoringIntent']['intent']
				if float(score)>=0.9:
					mail['intent'] = vals

'''