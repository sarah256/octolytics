import requests
import datetime
import dateutil.parser
import json


class LanguageLineCount():
	"""
	A class containing the functions for counting the number of
	lines a user has written in different languages.
	"""

	def get_commits(self, username):
		"""
		Get all of the recent commits a user has made.

		:param str username: the user we want to get data on
		:return: list of URLs to JSON data for each commit
		:rtype: list
		"""
		year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
		date = datetime.datetime.now()
		commits = []
		page = 1

		while date != year_ago:
			url = 'https://api.github.com/users/{0}/events?page={1}'.format(username, page)
			response = requests.get(url)
			events = json.loads(response.text)

			for event in events:
				if event['type'] == 'PushEvent':
					pushed_commits = event['payload']['commits']
					for commit in pushed_commits:
						commits.append(commit['url'])
			# import pdb;pdb.set_trace()
			print(type(events))
			last_event = events[-1]
			created_at = last_event['created_at']
			date = dateutil.parser.parse(created_at)
			page += 1

		return commits

	def get_line_counts(self, commits):
		"""
		Get the final count of the number of lines of code a user has
		written for a given file extension by processing each commit.

		:param list commits: a list of URLs, where each URL is a link
							 to the API JSON of a commit
		:return: A dictionary mapping a file extension with a number of
				 lines
		:rtype: dict
		"""
		return

	def format_file_extensions(self, mapping):
		"""
		Pair file extensions to their language names if there is one
		that the app stores.

		:param dict mapping: the mapping of file extensions with the
							 number of lines written with it
		:return: a dictionary with the file extension, line count,
				 and language name if there is one
		:rtype: dict
		"""
		return

class_instance = LanguageLineCount()
print(class_instance.get_commits('sarah256'))

