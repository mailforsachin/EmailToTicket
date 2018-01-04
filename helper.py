
import spacy
import numpy as np
import requests
def getContact(mailbox):
	return {'name':mailbox.name, 'email':mailbox.email_address}

def getContacts(mailboxes):
	return [getContact(i) for i in mailboxes]

pos = spacy.load('en')

def prob_block(sentence, pos_parser=pos):
	"""Calculate probability of email block.
	Parameters
	----------
	sentence : str
		Line in email block.
	pos_parser : obj
		A POS tagger object. This version relies on Spacy's English POS-tagger.
	Returns
	-------
	probability(signature block | line)
	"""
	try:
		sentence = unicode(sentence)
		parsed_data = pos_parser(sentence)
		for span in parsed_data.sents:
			sent = [parsed_data[i] for i in range(span.start, span.end)]
		non_verbs = np.sum([token.pos_ != 'VERB' for token in sent])
		total = len(sent)
		#print str(sentence) +"--"+ str(float(non_verbs) / total)
		return float(non_verbs) / total
	except Exception,e:
		return 0

def process(text,pos=pos):
	text = text.replace('\r','\n')
	text = text.split('\n')
	text = text[::-1]
	message = []
	temp = []
	disclaimer = False
	from_email = ''
	while True:
		try:
			line = text.pop().encode('ascii',errors = 'ignore')
			line = line.strip()
			nospace = line.replace(' ','')
			if line =='' or '-----' in line :
				continue
			if len(line.split()) == 1 and len(line)>10:
				continue
			if line[:6] == 'From: ':
				from_email = line[6:]
				disclaimer = False
				#msg_str = ' '.join(temp)
				message.append(temp)
				temp=[]
				#print line
			elif line[:4] == 'To: ' or line[:4] == 'Cc: ' or line[:9] == 'Subject: ' or line[:4] == 'Cc: ' or  line[:6] == 'Sent: ':
				#print line
				continue
			elif line.lower().find('disclaimer') == 0 or '__________' in line or line[0:].lower() in from_email.lower():
				disclaimer = True
				#print line
				continue
			elif line.lower().find('[cid:image') ==0:
				continue
			elif ('classification' in line.lower() or 'hello' in line.lower() or 'thank' in line.lower() or 'regard' in line.lower() or line[:4].lower() == 'best' or 'hi' in line.lower()) and prob_block(line,pos) >=0.9:
				continue
			elif (len(nospace) < 50 or '|' in line ) and prob_block(line,pos) >=0.9:
				continue
			elif disclaimer:
				#print line
				continue
			elif line == "\n":
				continue
			else:
				temp.append(line)
		except IndexError,e:
			break
		except Exception,e:
			print str(e)
			pass
	#msg_str = ' '.join(temp)
	message.append(temp)
	disclaimer = False
	return (message)


def getLuisIntent(utterance):
	luis_url = "https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/50e40c1c-efa2-48dd-bca3-d868ef5ed4c4?subscription-key=62ea92a6dad241628c1489c0333d166f&verbose=true&timezoneOffset=0&q=" + utterance[:500]
	res = requests.get(luis_url)
	if res.status_code == 200:
		vals = res.json()
		score = vals['topScoringIntent']['score']
		intent = vals['topScoringIntent']['intent']
		return (str(intent),float(score))

def getIntent(msgs):
	intents ={}
	for msg in msgs:
		utt = ' '.join(msg).strip()
		intent, score = getLuisIntent(utt)
		if score>0.9:
			return {'intent':intent,'utterance':utt}
			break

	return {'intent':None, 'utterance':None}

def getIntentPerLine(msgs):
	intent_dic = {}
	for msg in msgs:
		for line in msg:
			print line
			if prob_block(line) >=.6:
				intent, score = getLuisIntent(line)
				if score>0.85:
					if intent_dic.get(intent):
						intent_dic[intent].append(line)
					else:
						intent_dic[intent] = [line]
	return intent_dic



def pl(list):
	for i in list:
		print i