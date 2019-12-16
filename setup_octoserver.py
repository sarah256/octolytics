import re

from setuptools import setup

with open('req.txt', 'rb') as f:
    install_requires = f.read().decode('utf-8').split('\n')

setup(
    name='octoserver',
    description="Octolytics server!",
    author='Sarah Rieger, Sid Premkumar',
    author_email='sid.premkumar@gmai.com, sarah256@gmail.com',
    url='http://www.sarahrieger.net/, http://www.sarahrieger.net/',
    license='GNU',
    install_requires=install_requires,
    packages=[
        'octoserver',
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            "octoserver=octoserver.server:main",
        ],
    },
)