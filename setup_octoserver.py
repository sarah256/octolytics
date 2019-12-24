import re

from setuptools import setup

with open('req.txt', 'rb') as f:
    install_requires = f.read().decode('utf-8').split('\n')

setup(
    name='octolytics',
    description="Octolytics server!",
    author='Sarah Rieger, Sid Premkumar',
    author_email='sid.premkumar@gmail.com, sarah256@gmail.com',
    url='https://sidpremkumar.com/, http://www.sarahrieger.net/',
    license='GNU',
    install_requires=install_requires,
    packages=[
        'octolytics',
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            "octolytics=octolytics.server:main",
        ],
    },
)