# Built-In Modules
import os
import shlex
from datetime import datetime, timedelta
import subprocess
import re

# Local Modules
import server

# Global Variables
START_DATE = datetime.today() - timedelta(days=365)
FILE_TYPES = {
    'py': 'Python',
    'java': 'Java',
    'c': 'C',
    'cpp': 'C++',
    'go': 'Go',
    'html': 'HTML',
    'css': 'CSS',
    'js': 'JavaScript',
    'php': 'PHP',
    'ruby': 'Ruby',
    'cs': 'C#',
    'ts': 'TypeScript',
    'sh': 'Shell',
    'swift': 'Swift',
    'sc': 'Scala',
    'scala': 'Scala',
    'h': 'Objective C',
    'm': 'Objective C',
    'mm': 'Objective C',
    'M': 'Objective C',
}


class GitClient(object):
    """Git Object we are using to represent interactions with git."""

    def get_lines_for_repo(self, repo, username):
        """
        Get the total number of lines a user contributed to a repo by their
        file type.

        :param str repo: URL of git repo
        :param str username: the user we want data on
        :rtype: dict
        :return: dictionary with file types as keys, and line counts as values
        """
        line_counts = {}
        commits = get_commits(username, repo)

        for commit_hash in commits:
            for file_type in FILE_TYPES.keys():
                lines = get_lines_from_commit(commit_hash, file_type)
                line_counts[file_type] = lines
        
        return line_counts
    
    def get_lines_for_user(self, username):
        """
        Get the total number of lines a user contributed to all repos, by file
        type.

        :param str username: username of user 
        """


def clone_git_folder(url):
    """
    Clones just the .git folder of a url

    :param String url: URL of a git repo
    """
    # Build our args
    raw_args = f"git clone --no-checkout {url}"

    # Parse our args
    new_args = shlex.split((raw_args))

    # Call the git module
    try:
        response = subprocess.run(new_args, stdout=subprocess.PIPE)
        # Assert response was a sucsess
        # TODO:
    except Exception as e:
        print(f"Something went wrong cloning the git folder for url: {url}")

def get_commits(author, repo, start_date=START_DATE):
    """
    Gets all commits for an author

    :param String author: Author who we are looking for
    :param datetime start_date: The start date (in months) we go back
    :rtype: list(str)
    :return: list of commit hashes
    """
    # Build our args
    raw_args = f"git log --date=short --reverse --all " \
                f"--since={START_DATE.month}.months.ago --author={author}"

    # Parse our args
    new_args = shlex.split((raw_args))

    try:
        # Call the git module
        response = str(subprocess.run(new_args, stdout=subprocess.PIPE).stdout)

        # Extract out all the commits and return
        commits_unformatted = re.findall("commit [a-zA-Z0-9]+", response)

        # Return formatted commits
        return [x[7:] for x in commits_unformatted]
    except Exception as e:
        print(f"Something went wrong getting commits for {author}")

def get_lines_from_commit(commit_hash, file_type):
    """
    Get lines added for a specific file_type and commit_hash

    :param String commit_hash: Author who we are looking for
    :param String file_type: Type of file we are looking for (i.e. py)
    """
    # Build out args
    raw_args = f"git log {commit_hash} --numstat"

    # Parse our args
    new_args = shlex.split((raw_args))

    try:
        # Call the git module to get the number of lines changed
        response = str(subprocess.run(new_args, stdout=subprocess.PIPE).stdout)

        # Only calculate numbers that are in this commit
        # To limit, find the starting point of the next commit
        next_commit = ""
        if len(re.findall("commit [a-zA-Z0-9]+", response)) > 1:
            next_commit = re.findall("commit [a-zA-Z0-9]+", response)[1]

        # Loop over the files, adding lines if they mach file_type
        total_lines = 0
        for line in response.split('\\n'):
            # Check if we've passed our next commit
            if next_commit in line:
                break
            if file_type in line:
                # Extract the number of lines added (i.e. the first number)
                if re.search(f"[0-9]+", line):
                    total_lines += int(re.search('[0-9]+', line)[0])
        return total_lines
    except Exception as e:
        print(f"Something went wrong when getting the lines for hash {commit_hash}")
        return -1

if __name__ == "__main__":
    ret = get_commits('srieger')

    total_lines = 0
    for resp in ret:
        total_lines += get_lines_from_commit(resp, 'py')
    # ret = get_lines_from_commit(ret[0], 'py')
    print(total_lines)
