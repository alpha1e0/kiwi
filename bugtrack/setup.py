#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


from setuptools import setup, find_packages



setup(
    name="bugtrack",
    version="1.1",
    packages=find_packages()+['bugtrack.data.features.evals'],

    include_package_data = True,

    install_requires=[
        'appdirs>=1.4.0',
        'pyyaml>=3.11',
        'colorama>=0.3.7'
    ],

    author="alpha1e0",
    author_email="yan.shifm@foxmail.com",
    description="",
    keywords="security hacking audit",
    url="https://github.com/alpha1e0/bugtrack",

    entry_points = {
        'console_scripts': [
            'bugtrack = bugtrack.ui.cli.main:main',
            'bt-report-console = bugtrack.ui.webui.report_console:main'
        ],
    }
)