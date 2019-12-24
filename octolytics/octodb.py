# Local Modules
import os, logging, signal
from datetime import datetime

# 3rd Party Modules
from pymongo import MongoClient

# Create our logging
logging.basicConfig(format='%(message)s', level=logging.DEBUG)
log = logging.Logger('OCTODB')
log.setLevel(30)

# Create our database data
DB_NAME = os.environ['MONGO_NAME']
DB_HOST = 'ds053439.mlab.com'
DB_PORT = 53439
DB_USER = os.environ['MONGO_USER']
DB_PASS = os.environ['MONGO_PASS']

DATABASE_SCHEMA = {
    'username': None,
    'alias': None,
    'repos': None,
    # repo: { repo_name, repo_url }
    'repo_data': None,
    # repo_data: {'judymoses.github.io': {'.py': 50}}
    'badges': {},
    # badges: {'.py': (svg_file, datetime)}
    'sessions': {
        'email_code': (-1, datetime(1, 1, 1))
        # email_code: (code, datetime)
    }
}

class OctoDB(object):
    """This class will be our access to the database"""

    def __init__(self):
        """Make connection to DB"""
        # TODO: 60 second timeout to raise error
        # signal.alarm(60)
        try:
            connection = MongoClient(DB_HOST, DB_PORT, retryWrites=False)
            db = connection[DB_NAME]
            db.authenticate(DB_USER, DB_PASS)
            self.db_client = db.octolytics_data
        except Exception as e:
            logging.warning(f"Error connecting to database\nException: {e}")
            raise Exception("Timeout: Error connecting to database")

    def query_user(self, username):
        """
        Query the database for a user

        :param str username: username we're looking for
        :rtype Dict/None:
        :return: Dict of user data/None
        """
        # Get our users data, if they don't have any data create it
        if self.db_client.find_one({"username": username}):
            # Update a users data
            try:
                return self.db_client.find_one({"username": username})
            except Exception as e:
                logging.warning(f"Something went wrong when getting data for {username}.\nException: {e}")
                raise e

    def create_user(self, username, email):
        """
        Create a user in the database

        :param str username: Username we're creating
        :param str email: Email for the user
        :rtype Dict/Bool:
        :return: Dict/False if we created the user
        """
        # First make sure the user does not exists
        if self.query_user(username):
            logging.warning(f"[DB]: User {username} already exists")
        data = DATABASE_SCHEMA
        data['username'] = username
        data['alias'] = [email]
        try:
            self.db_client.insert_one(data)
            return data
        except Exception as e:
            logging.warning(f"Something went wrong when creating the user {username}.\nException: {e}")
            return False

    def update_user(self, username, user_data):
        """
        Update a users data

        :param str username:
        :param Dict user_data:
        """
        # Get the DB data
        db_data = self.db_client.find_one({"username": username})

        # Assert that the keys are the same - Sanity check
        if db_data.keys() != user_data.keys():
            raise Exception(f"Users db_keys != inserted keys - user: {username}")

        # Update
        self.db_client.update_one({'username': username}, {"$set": user_data}, upsert=False)
