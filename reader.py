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
credentials = Credentials(username='127334@nttdata.com', password='')

print "connecting to exchange"
account = Account(primary_smtp_address='127334@nttdata.com', credentials=credentials,autodiscover=True, access_type=DELEGATE)
print "connected"


unread  = account.inbox.filter(is_read=False).only('sender','to_recipients','cc_recipients','subject','datetime_received','text_body','body').order_by('-datetime_received')[:3]
#unread  = account.inbox.filter(is_read=False).order_by('-datetime_received')[:1]

emails = [i for i in unread]


#LUIS
luis_url = "https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/b922584b-1136-4b37-969e-9f0df9cb4579?subscription-key=62ea92a6dad241628c1489c0333d166f&verbose=true&timezoneOffset=330&q="

#MongoDB Connection
client = pymongo.MongoClient('mongodb://serivice-desk-store:pMzmGDeCcbMZEJ7hVirY9YEA7NMm6abpGF6oNz32D6MNTqsmdqzvdg3MLVw80eMlztxPP03vxsKxtatgPOiCFg==@serivice-desk-store.documents.azure.com:10255/?ssl=true&replicaSet=globaldb')
#client = pymongo.MongoClient('localhost', 27017)
db = client.hilton
sdmails  = db.emails

#Azure Service Bus Connection
nttBus = ServiceBusService(
    service_namespace='ntt-bus',
    shared_access_key_name='RootManageSharedAccessKey',
    shared_access_key_value='ak9L18tmI2FssJBIZLz3OCs8U55rcYZaSbwgAR6/B34=')



for email in emails:
	try:
		# Split and Parse emails
		# Get Contents
		# Save to db
		doc = {}
		doc['from'] = fx.getContact(email.sender)
		doc['to'] = fx.getContacts(email.to_recipients)
		if email.cc_recipients:
			doc['cc'] = fx.getContacts(email.cc_recipients) 
		doc['subject'] = email.subject.strip()
		msgs = fx.process(email.text_body)
		msgs = [[doc['subject']]] + msgs
		doc['emails'] = msgs
		doc['intent'] = fx.getIntent(msgs)
		#doc['intentions'] = fx.getIntentPerLine(msgs)
		doc['caseid'] = str(uuid.uuid4())
		doc['state'] = 'new'
		doc['handoff'] = False
		doc['botHasReplied'] = False
		#print docid
		
		#Send Message to Incoming Queue
		event = Message(json.dumps(doc))
		nttBus.send_queue_message('htn.incoming.emails', event)
		docid = sdmails.insert_one(doc).inserted_id
	except Exception,e:
		print email.subject
		print str(e)
		pass

