import requests
import datetime
import dateutil.parser
import json
from git_client import get_lines_from_commit, get_commits


class LanguageLineCount():
	"""
	A class containing the functions for counting the number of
	lines a user has written in different languages.
	"""
	languages = []

	def get_commits(self, username):
		"""
		Get all of the recent commits a user has made.

		:param str username: the user we want to get data on
		:return: list of URLs to JSON data for each commit
		:rtype: list
		"""
		

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

