#-*- coding:utf-8 -*-


'''
Btlime, a sublime plugin for finding security bugs.
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''

import os
import re
import yaml
import threading

import sublime
import sublime_plugin



class FileError(Exception):
    pass


class YamlConf(object):
    '''
    Yaml configure file loader
    '''
    def __new__(cls, path):
        try:
            _file = open(path,"r")
            result = yaml.load(_file)
        except IOError:
            raise FileError(
                "Loading yaml file '{0}' failed, read file failed".format(path))
        except yaml.YAMLError as error:
            raise FileError(
                "Loading yaml file '{0}' failed, yaml error, reason: '{1}'"\
                    .format(path,str(error)))
        except Exception as error:
            raise FileError("Loading yaml file '{0}' failed, reason: {1}"\
                .format(path,str(error)))

        return result


class Dict(dict):
    def __init__(self, *args, **kwargs):
        super(Dict, self).__init__(*args, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None

    def __setattr__(self, key, value):
        self[key] = value



def run_in_thread(wait=True):
    '''
    @params:
        wait: [True|False|timeout]，进程是否等待线程结束
    @returns:
        返回Queue.Queue
    '''
    def _wrapper(func):
        @functools.wraps(func)
        def threadFunc(*args, **kwargs):
            def run(queue, *args, **kwargs):
                ret = func(*args, **kwargs)
                queue.put(ret)

            queue = Queue.Queue()

            thread = threading.Thread(target=run, args=(queue, args), 
                kwargs=kwargs)

            thread.start()

            if wait is True:
                thread.join()
            elif isinstance(wait, float):
                thread.join(wait)

            return queue

        return threadFunc
    return _wrapper



class current(object):
    @classmethod
    def point(cls, view):
        return view.sel()[0].a


    @classmethod
    def region(cls, view):
        return view.sel()[0]


    @classmethod
    def regions(cls, view):
        return [r for r in view.sel()]


    @classmethod
    def scope(cls, view):
        return view.scope_name(view.sel()[0].a)


    @classmethod
    def word(cls, view):
        return view.substr(view.word(view.sel()[0]))


    @classmethod
    def rowcol(cls, view):
        point = view.sel()[0].a
        return view.rowcol(point)


    @classmethod
    def projectpath(cls, view):
        window = view.window()

        for folder in window.folders():
            if view.file_name().startswith(folder):
                return folder


    @classmethod
    def filename(cls, view):
        return view.file_name()


    @classmethod
    def basepath(cls, view):
        return os.path.dirname(view.file_name())


    @classmethod
    def filecontent(cls, view):
        return view.substr(sublime.Region(0,view.size()))


    @classmethod
    def pkgpath(cls):
        return os.path.dirname(__file__)





class RunBugtrackCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        proj_dir = args['dirs'][0]

        settings = sublime.load_settings('bugtrack.sublime-settings')
        btcmd = settings.get("bugtrack_command", "bugtrack")
        cachedir = settings.get("cache_directory_name", ".btlime-cache")
        
        self.run_bugtrack(btcmd, cachedir)

    def _run_bugtrack(self, btcmd, cachedir):
        pass



class ConfigBugtrackCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return



class GlobalCodeSearchCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return


#=====



class JumpLocationCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return



class SendtoTrashCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return



class SendtoReviewCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return



class CopyEntryCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return



class CutEntryCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return


#====


class ShowIssueCommand(sublime_plugin.TextCommand):
    ISSUEKEY = "btlime-issue"
    ISSUESCOPE = "invalid.illegal"

    def run(self, edit, **args):
        if self.view.get_regions(self.ISSUEKEY):
            self.view.erase_regions(self.ISSUEKEY)
            return
        else:
            regions = self._get_issue_regions()
            self.view.add_regions(self.ISSUEKEY, regions, self.ISSUESCOPE)


    def _load_config(self):
        if 'source.python' in current.scope(self.view):
            idfile = os.path.join(current.pkgpath(), 'issuedef', "python")
        elif 'source.java' in current.scope(self.view):
            idfile = os.path.join(current.pkgpath(), 'issuedef', "java")
        elif 'source.php' in current.scope(self.view):
            idfile = os.path.join(current.pkgpath(), 'issuedef', "php")
        else:
            idfile = None

        if idfile:
            return YamlConf(idfile)
        else:
            return None

    def _load_patterns(self):
        result = []
        config = self._load_config()
        if config:
            default_patterns = config.get('default-patterns',[])
            user_patterns = config.get('user-patterns',[])
            if isinstance(default_patterns, list):
                result = result + default_patterns
            if isinstance(user_patterns, list):
                result = result + user_patterns

        return result


    def _get_issue_regions(self):
        str_patterns = self._load_patterns()

        result = []
        patterns = [re.compile(p) for p in str_patterns]
        content = current.filecontent(self.view)

        for pattern in patterns:
            for match in pattern.finditer(content):
                if self.view.match_selector(match.start(), "comment"):
                    continue

                result.append(sublime.Region(match.start(),match.end()))

        return result

        



class FindForwardCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return


class FindFirstCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return



class RecordtoReviewCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return



class RecordtoTraceCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return



class CodeSearchCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return



#class GotoDefinationCommand(sublime_plugin.TextCommand):
#    def run(self, edit, **args):
#        return

