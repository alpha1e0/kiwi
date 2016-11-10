#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs
Copyright (c) 2016 alpha1e0
'''


from setuptools import setup, find_packages



setup(
    name="bugtrack",
    version="1.0",
    packages=find_packages(),

    install_requires=[
        'yaml>=0.3',
        'peewee'
    ],

    package_data={
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst'],
        # And include any *.msg files found in the 'hello' package, too:
        'hello': ['*.msg'],
    },

    # metadata for upload to PyPI
    author="alpha1e0",
    author_email="yan.shifm@foxmail.com",
    description="",
    keywords="security hacking",
    url="http://example.com/HelloWorld/",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)