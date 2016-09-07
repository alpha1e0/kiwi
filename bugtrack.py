#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
Copyright (c) 2016 alpha1e0
'''


import sys
import os
import re

import sublime
import sublime_plugin
import yaml

try:
    from libs.thirdparty import grin
except ImportError:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    from libs.thirdparty import grin



class CodeAnalysis(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        g = grin.GrepText(re.compile("grin_main"))
        o = g.do_grep(open("/Users/apple/tmp/grin-1.2.1/grin.py"))
        print(o)
        #print(args)

