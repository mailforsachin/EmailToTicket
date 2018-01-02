
import spacy
import numpy as np
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
	while True:
		try:
			line = text.pop().encode('ascii',errors = 'ignore')
			line = line.strip()
			nospace = line.replace(' ','')
			if line =='' or '-----' in line or '_____' in line:
				continue
			if len(line.split()) == 1 and len(line)>10:
				continue
			if line[:6] == 'From: ':
				disclaimer = False
				message.append(temp)
				temp=[]
				#print line
			elif line[:4] == 'To: ' or line[:4] == 'Cc: ' or line[:9] == 'Subject: ' or line[:4] == 'Cc: ' or  line[:6] == 'Sent: ':
				#print line
				continue
			elif line.lower().find('disclaimer') == 0:
				disclaimer = True
				#print line
				continue
			elif line.lower().find('[cid:image') ==0:
				continue
			elif ('classification' in line.lower() or 'hello' in line.lower() or 'thank' in line.lower() or 'regard' in line.lower() or line[:4].lower() == 'best' or 'hi' in line.lower()) and prob_block(line,pos) >=0.5:
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
	message.append(temp)
	disclaimer = False
	return (message)





def pl(list):
	for i in list:
		print i