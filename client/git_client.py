# Built-In Modules
import os
import shutil
import shlex
from datetime import datetime, timedelta
import subprocess
import re

# Global Variables
START_DATE = datetime.today() - timedelta(days=365)
FILE_TYPES = {
    '.py': 'Python',
    # '.java': 'Java',
    # '.c': 'C',
    # '.cpp': 'C++',
    # '.go': 'Go',
    # '.html': 'HTML',
    # '.css': 'CSS',
    # '.js': 'JavaScript',
    # '.php': 'PHP',
    # '.ruby': 'Ruby',
    # '.cs': 'C#',
    # '.ts': 'TypeScript',
    # '.sh': 'Shell',
    # '.swift': 'Swift',
    # '.sc': 'Scala',
    # '.scala': 'Scala',
    # '.h': 'Objective C',
    # '.m': 'Objective C',
    # '.mm': 'Objective C',
    # '.M': 'Objective C',
}


class GitClient(object):
    """Git object we are using to represent interactions with git."""

    def get_lines_for_repo(self, emails):
        """
        Get the total number of lines a user contributed to a repo by their
        file type.

        :param list(str) emails: The emails we're looking at
        :rtype: dict
        :return: dictionary with file types as keys, and line counts as values
        """
        line_counts = {}
        commits = get_latest_commits(emails)

        # For each commit hash, check if it should be counted
        for commit_hash in commits:
            for file_type in FILE_TYPES.keys():
                lines = get_lines_from_commit(commit_hash, file_type, emails)
                line_counts[file_type] = lines
        
        return line_counts

    def get_all_lines(self, emails, repos):
        """
        Get the total number of lines a user contributed to all repos, by file
        type.

        :param list(str) emails: List of emails we're looking at
        :param Dict repos: List of repo_name, repo_url from user
        :rtype Dict:
        :returns: Dict of calculated data: {'judymoses.github.io': {'.py': 50}}
        """
        if "/temp" not in str(subprocess.run(['pwd'], stdout=subprocess.PIPE).stdout):
            # Change directory
            os.chdir("client/temp/")

            if "/temp" not in str(subprocess.run(['pwd'], stdout=subprocess.PIPE).stdout):
                raise Exception("Cant cd into /temp Folder")

        # Loop over the repos and save
        repo_data = {}
        for repo_name, repo_url in repos.items():
            # Clone .git file
            clone_git_folder(repo_url)

            # Change directory
            os.chdir(repo_name)

            repo_data[repo_name] = self.get_lines_for_repo(emails)

            # Get out and delete
            os.chdir("..")
            shutil.rmtree(repo_name)
        
        # Get out of temp
        os.chdir("..")

        # We need to update "ALL" in repo_data
        repo_data["ALL"] = FILE_TYPES
        for repo_name, repo_stats in repo_data.items():
            for file_type in FILE_TYPES.keys():
                if type(repo_data["ALL"][file_type]) is int:
                    repo_data["ALL"][file_type] += repo_stats.get(file_type, 0)
                else:
                    repo_data["ALL"][file_type] = repo_stats.get(file_type, 0)

        return repo_data


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


def get_latest_commits(emails, start_date=START_DATE):
    """
    Gets all commits for all aliases (emails)

    :param list(str) emails: Emails who we are looking for
    :param datetime start_date: The start date (in months) we go back
    :rtype: list(str)
    :return: list of commit hashes
    """
    # Build our args
    raw_args = f"git log --date=short --all " \
                f"--since={start_date.month}.months.ago --pretty=format:\"%ae;%H\""

    # Parse our args
    new_args = shlex.split((raw_args))

    # Check if its the email we're looking for
    try:
        # Call the git module
        response = str(subprocess.run(new_args, stdout=subprocess.PIPE).stdout)
        # Loop and check if its the email, add commit
        commits = []
        for line in response.split("\\n"):
            if line[0:line.find(';')] in emails:
                # Extract out all the commits and return
                commits.append(line[line.find(';')+1:])
                break
        return commits

    except Exception as e:
        print(f"Something went wrong getting commits for {author}")
        return []


def get_lines_from_commit(commit_hash, file_type, emails):
    """
    Get lines added for a specific file_type and commit_hash

    :param list(str) emails: Emails who we are looking for
    :param String commit_hash: Author who we are looking for
    :param String file_type: Type of file we are looking for (i.e. py)
    """
    # Build out args
    raw_args = f"git log {commit_hash} --numstat " \
               f"--pretty=\"%ae---\" --since={START_DATE.month}.months.ago"

    # Parse our args
    new_args = shlex.split((raw_args))

    try:
        # Call the git module to get the number of lines changed
        response = str(subprocess.run(new_args, stdout=subprocess.PIPE).stdout)

        # Loop over files and count lines
        total_lines = 0
        add_to_lines = False
        while True:
            line = response.stdout.readline()
            if not line:
                break
            line = line.replace("\n", "").replace("\t", " ")
            if check_line_for_emails(line, emails):
                add_to_lines = True
            elif '---' in line:
                add_to_lines = False
            if add_to_lines and '---' not in line and line.endswith(file_type):
                #TODO: handle case when commit message/line may end in file extension
                # Extract the number of lines added (i.e. the first number)
                # Get the first number and add to total_lines
                total_lines += int(line.split(" ")[0])

        return total_lines
    except Exception as e:
        print(f"Something went wrong when getting the lines for hash {commit_hash}")
        return -1


def check_line_for_emails(line, emails):
    """
    Helper function to see if any email is in the line
    :param str line: Output line
    :param list(str) emails: List of emails we're looking for
    :rtype Boolean:
    :return: True/False
    """
    for email in emails:
        if email in line:
            #TODO: handle case when email might be in commit message
            return True
    return False

# if __name__ == "__main__":
#     # ret = get_commits('srieger')
#     #
#     # total_lines = 0
#     # for resp in ret:
#     #     total_lines += get_lines_from_commit(resp, 'py')
#     # # ret = get_lines_from_commit(ret[0], 'py')
#     # print(total_lines)
#     client = GitClient()
#     client.get_all_lines('sidpremkumar', {'judymoses.github.io': 'git://github.com/judymoses/judymoses.github.io.git'})
