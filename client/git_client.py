# Build-In Modules
import os
import shlex
from datetime import datetime, timedelta
import subprocess
import re

# Global Variables
START_DATE = datetime.today() - timedelta(days=365)


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

def get_commits(author, start_date=START_DATE):
    """
    Gets all commits for an author

    :param String author: Author who we are looking for
    :param datetime start_date: The start date (in months) we go back
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
    Get lines added for a spesific file_type and commit_hash

    :param String commit_hash: Author who we are looking for
    :param String file_type: Type of file we are looking for (i.e. py)
    """
    # Build out args
    raw_args = f"git diff --numstat {commit_hash}"

    # Parse our args
    new_args = shlex.split((raw_args))

    try:
        # Call the git module
        response = str(subprocess.run(new_args, stdout=subprocess.PIPE).stdout)

        # Loop over the files, adding lines if they mach file_type
        total_lines = 0
        for file in response.split('\n'):
            if file_type in file:
                # Extract the number of lines added (i.e. the first number)
                if re.search(f"[0-9]+", file):
                    total_lines += int(re.search('[0-9]+', file)[0])
        return total_lines
    except Exception as e:
        print(f"Something went wrong when getting the lines for hash {commit_hash}")
        return -1

if __name__ == "__main__":
    ret = get_commits('Sidhartha\ Premkumar')

    ret = get_lines_from_commit(ret[0], 'py')
    print(ret)
