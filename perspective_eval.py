'''
This file contains code to run the Perspective comment analyzer
on a snippet of text.
'''

import requests
import json
import os
import pandas as pd
from tqdm import tqdm
import time
from random import shuffle

def eval_text(text, retry=1):
	# This is the URL which Perspective API requests go to.
	PERSPECTIVE_URL = 'https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze'
	key = "AIzaSyBT0no02hmXlqQIubI9wjeX7QAdSrfp_wQ"; # TODO: fill this in with your Perspective API Key!

	url = PERSPECTIVE_URL + '?key=' + key
	data_dict = {
		'comment': {'text': text},
		'languages': ['en'],
		# This dictionary specifies which attributes you care about. You are welcome to (and should) add more.
		# The full list can be found at: https://github.com/conversationai/perspectiveapi/blob/master/2-api/models.md
		'requestedAttributes': { 'TOXICITY': {} },
		'doNotStore': True
	}

	while True:
		response = requests.post(url, data=json.dumps(data_dict))
		response_dict = response.json()

		if "attributeScores" in response_dict:
			break
		
		if retry == -1:
			raise Exception("Invalid reponse from API (probably polling too fast)")

		time.sleep(retry)

	return response_dict["attributeScores"]["TOXICITY"]["summaryScore"]["value"]


def find_anomalies(tweets, anomalous_above_threshold, threshold=0.5, max_num=5, gui=True):
	anomalies = []
	if gui:
		pbar = tqdm(total=max_num)
	for i, tweet in enumerate(tweets):
		score = eval_text(tweet)

		if gui:
			pbar.set_description("Made %d requests" % (i + 1))

		if (anomalous_above_threshold and score > threshold) or (not anomalous_above_threshold and score < threshold):
			anomalies.append((tweet, score))
			if gui:
				pbar.update(1)
			if not max_num is None and len(anomalies) >= max_num:
				break

		time.sleep(0.5)
	return anomalies

# https://github.com/t-davidson/hate-speech-and-offensive-language
# df = pd.read_csv("hate-speech-and-offensive-language/data/labeled_data.csv")
# clean = df[df['class'] == 2]['tweet'].to_list()
# dirty = df[df['class'] != 2]['tweet'].to_list()
# shuffle(clean)
# shuffle(dirty)
# anomalies = find_anomalies(clean, True, threshold=0.7) + find_anomalies(dirty, False, threshold=0.3)
# print(anomalies)

# https://github.com/aitor-garcia-p/hate-speech-dataset
def read_data():
	path = "hate-speech-dataset/"
	comments_good = []
	comments_bad = []
	#reads in csv annotations to sort text
	df = pd.read_csv(path + "annotations_metadata.csv")
	good_fileID = df[df['label'] == 'noHate']['file_id'].to_list()
	bad_fileID = df[df['label'] == 'hate']['file_id'].to_list()

	for filename in os.listdir(path + 'all_files/'):
		file = open(path + 'all_files/' + filename)
		text = file.read()
		if os.path.splitext(filename)[0] in good_fileID:
			comments_good.append(text)
		else:
			comments_bad.append(text)

		file.close()

	return comments_good, comments_bad

clean2, dirty2 = read_data()
shuffle(clean2)
shuffle(dirty2)
anomalies2 = find_anomalies(clean2, True, threshold=0.7) + find_anomalies(dirty2, False, threshold=0.3)
print(anomalies2)