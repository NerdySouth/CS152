import os
import time
import re
import requests # *
import json
from slackclient import SlackClient # *

# These are personalized tokens - you should have configured them yourself
# using the 'export' keyword in your terminal.
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')
PERSPECTIVE_KEY = os.environ.get('PERSPECTIVE_KEY')

if (SLACK_BOT_TOKEN == None or SLACK_API_TOKEN == None): #or PERSPECTIVE_KEY == None):
	print("Error: Unable to find environment keys. Exiting.")
	exit()

# Instantiate Slack clients
# bot_slack_client = slack.WebClient(token=SLACK_BOT_TOKEN)
# api_slack_client = slack.WebClient(token=SLACK_API_TOKEN)
bot_slack_client = SlackClient(SLACK_BOT_TOKEN)
api_slack_client = SlackClient(SLACK_API_TOKEN)
# Reportbot's user ID in Slack: value is assigned after the bot starts up
reportbot_id = None

# Constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
REPORT_COMMAND = "report"
CANCEL_COMMAND = "cancel"
HELP_COMMAND = "help"

#Broad Categories for Reporting
HARASS_COMMAND = "harass"
SUICIDE_COMMAND = "suicide"
SPAM_COMMAND = "spam"
NUDE_COMMAND = "nude"
VIOLENCE_COMMAND = "violence"
SCAM_COMMAND = "scam"
OTHER_COMMAND = "other"


# Possible report states - saved as strings for easier debugging.
STATE_REPORT_START 		 = "report received" 	# 1
STATE_MESSAGE_IDENTIFIED = "message identified" # 2
STATE_CATEGORY_CHOSEN = "the user chose a category" #3


# Currently managed reports. Keys are users, values are report state info.
# Each report corresponds to a single message.
reports = {}


def handle_slack_events(slack_events):
	'''
	Given the list of all slack events that happened in the past RTM_READ_DELAY,
	this function decides how to handle each of them.

	DMs - potential report
	Public IM - post Perspective score in the same channel
	'''
	for event in slack_events:
		# Ignore other events like typing or reactions
		if event["type"] == "message" and not "subtype" in event:
			if (is_dm(event["channel"])):
				# May or may not be part of a report, but we need to check
				replies = handle_report(event)
			else:
				# Send all public messages to perspective for review
				scores = eval_text(event["text"], PERSPECTIVE_KEY)

				#############################################################
				# STUDENT TODO: currently this always prints out the scores.#
				# You probably want to change this behavior!                #
				#############################################################
				replies = [format_code(json.dumps(scores, indent=2))]

			# Send bot's response(s) to the same channel the event came from.
			for reply in replies:
				bot_slack_client.api_call(
				    "chat.postMessage",
				    channel=event["channel"],
				    text=reply
				)


def handle_report(message):
	'''
	Given a DM sent to the bot, decide how to respond based on where the user
	currently is in the reporting flow and progress them to the next state
	of the reporting flow.
	'''
	user = message["user"]

	if HELP_COMMAND in message["text"]:
		return response_help()

	# If the user isn't in the middle of a report, check if this message has the keyword "report."
	if user not in reports:
		if not REPORT_COMMAND in message["text"]:
			return []

		# Add report with initial state.
		reports[user] = {"state" : STATE_REPORT_START}
		return response_report_instructions()

	# Otherwise, we already have an ongoing conversation with them.
	else:
		if CANCEL_COMMAND in message["text"]:
			reports.pop(user) # Remove this report from the map of active reports.
			return ["Report cancelled."]

		report = reports[user]

		####################################################################
		# STUDENT TODO:                                                    #
		# Here's where you should expand on the reporting flow and build   #
		# in a progression. You're welcome to add branching options and    #
		# the like. Get creative!                                          #
		####################################################################

		if report["state"] == STATE_REPORT_START:
			# Fill in the report with reported message info.
			result = populate_report(report, message)

			# If we received anything other than None, it was an error.
			if result:
				reports.pop(user)
				return result

			# Progress to the next state.
			report["state"] = STATE_MESSAGE_IDENTIFIED
			return response_identify_message(user)

		elif report["state"] == STATE_MESSAGE_IDENTIFIED:

			if HARASS_COMMAND in message["text"]:
				#TODO: fill in sub categories!: "Hate Speech/Symbols, Bullying, None of these, but I'd like to tell you more..."
				return response_what_next()
			elif SUICIDE_COMMAND in message["text"]:
				#TODO: fill in sub categories!: "Person who wrote the message is encouraging me/someone else to harm myself/themselves, 
				# "Person who wrote the message is encouraging me/someone else to commit suicide, 
				# "Person who wrote the message is at risk of suicide, 
				# "Person who wrote the message is at risk of self-harm
				# "None of these, but I'd like to tell you more..."
				# (note: made modifications to include "me/someone else" b/c not just a direct message anymore like FB Messenger)
				return report_suicide()
			elif SPAM_COMMAND in message["text"]:
				#TODO: no subcategories, lead directly to next stage....
				return response_what_next()
			elif NUDE_COMMAND in message["text"]:
				#TODO: fill in sub categories!: "Child sexual exploitation/imagery/abuse, Sexual exploitation or solicitation, 
				# "Nudity or pornography, None of these, but I'd like to tell you more..."
				return response_what_next()
			elif VIOLENCE_COMMAND in message["text"]:
				#TODO: fill in sub categories!: "Dangerous Organizations, Specific threats of harm, Extreme graphic violence,
				# "None of these, but I'd like to tell you more..."
				return response_what_next()
			elif SCAM_COMMAND in message["text"]:
				#TODO: fill in sub categories!: "False information, Financial Scam, Impersonation (of me/someone I know), 
				# "None of these, but I'd like to tell you more..."
				return response_what_next()
			else:
				#TODO: the user wants to report something not in the broad categories...take them to stage to explain more
				return response_what_next()
			# What was originally under the "elif report["state"]" line"
			# return response_what_next()

			# TODO: (if time) show a dialog instead? 
			# See https://github.com/slackapi/python-dialog-example/blob/master/example.py
			# open_dialog = api_slack_client.api_call(
			# 	"dialog.open",
			# 	#trigger_id=message["trigger_id"],
			# 	dialog={
			# 			"title": "Report a message",
			# 			"submit_label": "Submit",
			# 			"callback_id": user + "report_form",
			# 			"elements": [
			# 				{
			# 					"label": "Why are you reporting this message?",
			# 					"type": "select",
			# 					"name": "reporting_categories",
			# 					"placeholder": "Category",
			# 					"options": [
			# 						{
			# 							"label": "Harassment",
			# 							"value": "harassment"
			# 						},
			# 						{
			# 							"label": "Suicide/Self-Harm",
			# 							"value": "latte"
			# 						},
			# 						{
			# 							"label": "Pour Over",
			# 							"value": "pour_over"
			# 						},
			# 						{
			# 							"label": "Cold Brew",
			# 							"value": "cold_brew"
			# 						}
			# 					]
			# 				}
			# 			]
			# 		}
			# 	)

			# print(open_dialog)


def response_help():
	reply =  "Use the `report` command to begin the reporting process.\n"
	reply += "Use the `cancel` command to cancel the report process.\n"
	return [reply]


def response_report_instructions():
	reply =  "Thank you for starting the reporting process. "
	reply += "Say `help` at any time for more information.\n\n"
	reply +=  "Please copy paste the link to the message you want to report.\n"
	reply += "You can obtain this link by clicking on the three dots in the" \
		  +  " corner of the message and clicking `Copy link`."
	return [reply]


def response_identify_message(user):
	replies = []
	report = reports[user]

	reply =  "I found the message "
	reply += format_code(report["text"])
	reply += " from user " + report["author_full"]
	reply += " (" + report["author_name"] + ").\n\n"
	replies.append(reply)

	#TODO: Flesh out these reporting categories?/Make them "clickable"/reactions?
	reply = "_Why are you reporting this message?_\n"
	reply += "Type `harass` if you want to report this message for _Harassment_.\n"
	reply += "Type `suicide` if you want to report this message for _Suicide/Self-Harm_.\n"
	reply += "Type `spam` if you want to report this message for _Spam_.\n"
	reply += "Type `nude` if you want to report this message for _Nudity/Sexual Activity_.\n"
	reply += "Type `violence` if you want to report this message for _Violence_.\n"
	reply += "Type `scam` if you want to report this message for _Scam/Fraud_.\n"
	reply += "Type `other` if you want to report this message but it does not fall under the above categories.\n"
	reply += "Use the `cancel` command to cancel the report process.\n"
	replies.append(reply)

	#TODO: remove, Original contents of this function
	# reply =  "_This is as far as the bot knows how to go - " \
	# 	  +  "it will be up to students to build the rest of this process._\n"
	# reply += "Use the `cancel` keyword to cancel this report."
	# replies.append(reply)

	return replies


def response_what_next():
	reply =  "_This is as far as the bot knows how to go._\n"
	reply += "Use the `cancel` keyword to cancel this report."
	return [reply]

def report_suicide():
	reply =  "Thank you for reporting this message. We value your feedback.\n"
	reply += "We are only a chat application and can't give you answers to your "\
	      + "questions, but we do want you to help you find the support you need.\n\n"
	reply += "*_Need to talk to someone?_*\n"
	reply += "	_National Suicide Prevention Hotline: *1-800-273-8255*_\n"
	reply += "	_National Suicide Prevention Online Chat:_ <https://suicidepreventionlifeline.org/chat/>\n"
	reply += "	_Message a trust person from my contacts:_ <https://google.com>\n" #TODO: fill in!

	reply += "*_Don't want to receive messages from this person anymore?_*\n"
	reply += "	_Block this user_\n" #TODO: fill in the actual user's name
	reply += "*_What can I do if the message is still bothering me?_*\n"
	reply += "	_TODO: FILL IN_\n" #TODO: fill in! I'm not sure what option we want to give them
	return [reply]

def report_csam():
	#TODO: edit for CSAM
	reply =  "Thank you for reporting this message. We value your feedback.\n"
	reply += "We are only a chat application and can't give you answers to your "\
	      + "questions, but we do want you to help you find the support you need.\n\n"
	reply += "*_Need to talk to someone?_*\n"
	reply += "	_National Suicide Prevention Hotline: *1-800-273-8255*_\n"
	reply += "	_National Suicide Prevention Online Chat:_ <https://suicidepreventionlifeline.org/chat/>\n"
	reply += "	_Message a trust person from my contacts:_ <https://google.com>\n" #TODO: fill in!

	reply += "*_Don't want to receive messages from this person anymore?_*\n"
	reply += "	_Block this user_\n" #TODO: fill in the actual user's name
	reply += "*_What can I do if the message is still bothering me?_*\n"
	reply += "	_TODO: FILL IN_\n" #TODO: fill in! I'm not sure what option we want to give them
	return [reply]



###############################################################################
# UTILITY FUNCTIONS - you probably don't need to read/edit these, but you can #
# if you're curious!														  #
###############################################################################


def populate_report(report, message):
	'''
	Given a URL of some message, parse/lookup:
	- ts (timestamp)
	- channel
	- author_id (unique user id)
	- author_name
	- author_full ("real name")
	- text
	and save all of this info in the report.
	'''
	report["ts"],     \
	report["channel"] \
	= parse_message_from_link(message["text"])

	if not report["ts"]:
		return ["I'm sorry, that link was invalid. Report cancelled."]

	# Specifically have to use api slack client
	found = api_slack_client.api_call(
		"conversations.history",
		channel=report["channel"],
		latest=report["ts"],
		limit=1,
		inclusive=True
	)

	# If the key messages isn't in found, odds are we are missing some permissions.
	if "messages" not in found:
		print(json.dumps(found, indent=2))
		return ["I'm sorry, I don't have the right permissions too look up that message."]

	if len(found["messages"]) < 1:
		return ["I'm sorry, I couldn't find that message."]

	reported_msg = found["messages"][0]
	if "subtype" in reported_msg:
		return ["I'm sorry, you cannot report bot messages at this time."]
	report["author_id"] = reported_msg["user"]
	report["text"] = reported_msg["text"]

	author_info = bot_slack_client.api_call(
		"users.info",
		user=report["author_id"]
	)
	report["author_name"] = author_info["user"]["name"]
	report["author_full"] = author_info["user"]["real_name"]


def is_dm(channel):
	'''
	Returns whether or not this channel is a private message between
	the bot and a user.
	'''
	response = bot_slack_client.api_call(
		"conversations.info",
		channel=channel,
		include_num_members="true"
	)
	channel_info = response["channel"]

	# If this is an IM with only two people, necessarily it is someone DMing us.
	if channel_info["is_im"] and channel_info["num_members"] == 2:
		return True
	return False


def parse_message_from_link(link):
	'''
	Parse and return the timestamp and channel name from a message link.
	'''
	parts = link.strip('>').strip('<').split('/') # break link into meaningful chunks
	# invalid link
	if len(parts) < 2:
		return None, None
	ts = parts[-1][1:] # remove the leading p
	ts = ts[:10] + "." + ts[10:] # insert the . in the correct spot
	channel = parts[-2]
	return ts, channel


def eval_text(message, key):
	'''
	Given a message and a perspective key, forwards the message to Perspective
	and returns a dictionary of scores.
	'''
	PERSPECTIVE_URL = 'https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze'

	url = PERSPECTIVE_URL + '?key=' + key
	data_dict = {
		'comment': {'text': message},
		'languages': ['en'],
		'requestedAttributes': {
								'SEVERE_TOXICITY': {}, 'PROFANITY': {},
								'IDENTITY_ATTACK': {}, 'THREAT': {},
								'TOXICITY': {}, 'FLIRTATION': {}
							   },
		'doNotStore': True
	}
	response = requests.post(url, data=json.dumps(data_dict))
	response_dict = response.json()

	scores = {}
	for attr in response_dict["attributeScores"]:
		scores[attr] = response_dict["attributeScores"][attr]["summaryScore"]["value"]

	return scores


def format_code(text):
	'''
	Code format messages for Slack.
	'''
	return '```' + text + '```'

def main():
	'''
	Main loop; connect to slack workspace and handle events as they come in.
	'''
	if bot_slack_client.rtm_connect(with_team_state=False):
		print("Report Bot connected and running! Press Ctrl-C to quit.")
		# Read bot's user ID by calling Web API method `auth.test`
		reportbot_id = bot_slack_client.api_call("auth.test")["user"]
		while True:
			handle_slack_events(bot_slack_client.rtm_read())
			time.sleep(RTM_READ_DELAY)
	else:
		print("Connection failed. Exception traceback printed above.")


# Main loop
if __name__ == "__main__":
    main()
