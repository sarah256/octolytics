# 3rd Party Modules
from pybadges import badge

# Global Variables
FILE_TYPES = {
    '.py': 'Blue',
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


class BadgeMaker(object):
    """Object to make badges for us."""
    def make_badge(self, repo_data, file_type):
        """
        Function to make a badge for file_type using repo_data

        :param dict repo_data: Repo data for the user
        :param str file_type: File type (i.e. .py)
        :rtype img:
        :return: Badge
        """
        # Round our number first
        rounded_number = float(repo_data[file_type] / 1000)
        rounded_number = repr(round(rounded_number, 2))
        return badge(left_text=file_type[1:], right_text=f"{rounded_number}K", right_color=FILE_TYPES[file_type])
