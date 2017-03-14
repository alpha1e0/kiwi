#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import sys
import os
import re

import sublime
import sublime_plugin
import yaml

#try:
#    import libs
#except ImportError:
#    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
#    
#from libs.analyzer import Analyzer
#from libs.commons import CacheManage
#from libs.commons import runInThread
#from libs.commons import conf



#class SecurityAnalysisCommand(sublime_plugin.TextCommand):
#    def run(self, edit, **args):
#        projDir = args['dirs'][0]#

#        self.doAnalyse(projDir, sublime)#
#

#    @runInThread
#    def doAnalyse(self, projDir, sublimeObj):
#        settings = sublime.load_settings('bugtrack.sublime-settings')
#        cacheDirName = settings.get("cache_directory_name", ".cache")
#        try:
#            analyzer = Analyzer(projDir)
#            result = analyzer.doAnalyse()#

#            cachem = CacheManage(projDir, cacheDirName)#

#            resultFile = os.path.basename(projDir) + ".bugtrack"
#            cachem.addFile(resultFile,result.toString())
#        except Exception as error:
#            sublimeObj.error_message(str(error))#
#
#

#class ResultJumpCommand(sublime_plugin.TextCommand):
#    def run(self, edit):
#        for sel in self.view.sel():
#            line_number = self._get_line_number(sel)
#            file_name = self._get_file_name(sel)#

#            if line_number and file_name:
#                file_loc = "{0}:{1}".format(file_name, line_number)
#                self.view.window().open_file(file_loc, sublime.ENCODED_POSITION)
#            elif file_name:
#                self.view.window().open_file(file_name)#
#

#    def _match_line_number(self, line):
#        line_number_pattern = re.compile(r"^\s*(\d+):.*")
#        match = line_number_pattern.match(line)
#        
#        return match.group(1) if match else None#
#

#    def _match_file_name(self, line):
#        file_name_pattern = re.compile(r"^@(.+):$")
#        match = file_name_pattern.match(line)#

#        return match.group(1) if match else None#
#

#    def _get_line_number(self, sel):
#        line_text = self.view.substr(self.view.line(sel))#

#        return self._match_line_number(line_text)#
#

#    def _get_file_name(self, sel):
#        line_region = self.view.line(sel)
#        line_text = self.view.substr(line_region)#

#        match = self._match_file_name(line_text)
#        if match:
#            if os.path.exists(match):
#                return match
#        else:
#            match = self._match_line_number(line_text)
#            if match:
#                while line_region.begin() > 0:
#                    line_text = self.view.substr(line_region)
#                    match = self._match_file_name(line_text)#

#                    if match:
#                        if os.path.exists(match):
#                            return match#

#                    line_region = self.view.line(line_region.begin() - 1)#

#        return None



#class BugtrackColorSchemeCommand(sublime_plugin.EventListener):
#    def _is_bugtrack_result_view(self, view):
#        syntax = view.settings().get('syntax')
#        if syntax and syntax.endswith("bugtrack.sublime-syntax"):
#            return True
#        else:
#            return False#

#    def _load_color_scheme(self, settings, view):
#        color_scheme = settings.get('analyse_result_color_scheme')
#        if color_scheme:
#            view.settings().set('color_scheme', color_scheme)#
#

#    def _set_read_only(self, settings, view):
#        readonly = settings.get('analyse_result_read_only', True)
##        if readonly:
##            view.set_read_only(True)#
#
#

#    def on_activated_async(self, view):
#        if self._is_bugtrack_result_view(view):
#            settings = sublime.load_settings('bugtrack.sublime-settings')
#            self._load_color_scheme(settings, view)
#            self._set_read_only(settings, view)
#            #

#    def on_deactivated_async(self, view):
#        if self._is_bugtrack_result_view(view):
#            view.set_read_only(False)

