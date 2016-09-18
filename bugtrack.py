#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
-----------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import sys
import os
import re

import sublime
import sublime_plugin
import yaml

try:
    import libs
except ImportError:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    
from libs.analyse import FileSet
from libs.commons import CacheManage
from libs.commons import threadTask



class CodeAnalysisCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        projDir = args['dirs'][0]

        self.doAnalyse(projDir, sublime)


    @threadTask
    def doAnalyse(self, projDir, sublimeObj):
        try:
            fileset = FileSet(projDir)
            result = fileset.doAnalyse()

            cachem = CacheManage(projDir)
            resultFile = os.path.basename(projDir) + ".bugtrack"
            cachem.addFile(resultFile,result.toString())
        except Exception as error:
            sublimeObj.error_message(str(error))



class ResultJumpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            line_no = self._get_line_no(sel)
            file_name = self._get_file_name(sel)

            if line_no and file_name:
                file_loc = "{0}:{1}".format(file_name, line_no)
                self.view.window().open_file(file_loc, sublime.ENCODED_POSITION)
            elif file_name:
                self.view.window().open_file(file_name)


    def _get_line_no(self, sel):
        line_text = self.view.substr(self.view.line(sel))
        match = re.match(r"\s*(\d+).+", line_text)

        return match.group(1) if match else None


    def _get_file_name(self, sel):
        line = self.view.line(sel)

        while line.begin() > 0:
            line_text = self.view.substr(line)
            match = re.match(r"(.+):$", line_text)

            if match:
                if os.path.exists(match.group(1)):
                    return match.group(1)

            line = self.view.line(line.begin() - 1)

        return None



class BugtrackColorSchemeCommand(sublime_plugin.EventListener):
    def _is_bugtrack_result_view(self, view):
        syntax = view.settings().get('syntax')
        if syntax and syntax.endswith("bugtrack.sublime-syntax"):
            return True
        else:
            return False

    def _load_color_scheme(self, settings, view):
        color_scheme = settings.get('analyse_result_color_scheme')
        if color_scheme:
            view.settings().set('color_scheme', color_scheme)


    def _set_read_only(self, settings, view):
        readonly = settings.get('analyse_result_read_only', True)
        if readonly:
            view.set_read_only(True)



    def on_activated_async(self, view):
        if self._is_bugtrack_result_view(view):
            settings = sublime.load_settings('bugtrack.sublime-settings')
            self._load_color_scheme(settings, view)
            self._set_read_only(settings, view)
            

    def on_deactivated_async(self, view):
        if self._is_bugtrack_result_view(view):
            view.set_read_only(False)

