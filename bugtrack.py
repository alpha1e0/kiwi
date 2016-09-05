#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
Copyright (c) 2016 alpha1e0
'''


import sublime
import sublime_plugin

import yaml

from libs.thirdparty import grin

class CodeAnalysis(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        grin.grin_main(['bugtrack', 'os.system'])
        print(args)

