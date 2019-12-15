import requests
from flask import Flask, render_template, redirect
from flask_github import Github


app = Flask(__name__)
# TODO: register https://github.com/settings/applications/new once we
# have a URL to get these (I think)
app.config['GITHUB_CLIENT_ID'] = 'XXX'
app.config['GITHUB_CLIENT_SECRET'] = 'YYY'

app.config['GITHUB_AUTH_URL'] = 'https://github.com/login/oauth/authorize'

github = GitHub(app)

@app.route("/login")
def get_github_auth():
    """
    Get the user's authentication through Github.
    
    :rtype: auth page
    :return: the Github auth page
    """
    return github.authorize()


if __name__ == '__main__':
    app.run()
