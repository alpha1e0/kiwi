#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Kiwi, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


from setuptools import setup, find_packages



setup(
    name="kiwi",
    version="1.1",

    packages = find_packages(),
    include_package_data = True,

    install_requires=[
        'appdirs>=1.4.0',
        'pyyaml>=3.11',
        'colorama>=0.3.7',
        'flask>=0.12.2',
        'eventlet>=0.21.0',
        'jinja2>=2.7.3'
    ],

    author="alpha1e0",
    author_email="yan.shifm@foxmail.com",
    description="",
    keywords="security hacking audit",
    url="https://github.com/alpha1e0/kiwi",

    entry_points = {
        'console_scripts': [
            'kiwi = kiwi.ui.cli.main:main',
            'kiwi-report = kiwi.ui.webui.report_console:main'
        ],
    }
)