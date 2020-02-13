'''
This file contains code to run the Perspective comment analyzer
on a snippet of text.
'''

import requests
import json

def eval_text(text):
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
	response = requests.post(url, data=json.dumps(data_dict))
	response_dict = response.json()

	# Print the entire response dictionary.
	print("\"" + text + "\"")
	print(json.dumps(response_dict, indent=4))


# Here you can add code to evaluate particular messages.
eval_text("As an example: am I toxic?")
