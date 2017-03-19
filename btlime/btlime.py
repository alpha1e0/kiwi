#-*- coding:utf-8 -*-


'''
Btlime, a sublime plugin for finding security bugs.
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''

import os
import re
import yaml
import time
import threading
import subprocess

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



def run_in_thread(func):
    def thread_func(*args, **kwargs):
        def run():
            r = func(*args, **kwargs)

        t = threading.Thread(target=run)
        t.start()

    return thread_func



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
    def filepath(cls, view):
        return os.path.dirname(view.file_name())


    @classmethod
    def filecontent(cls, view):
        return view.substr(sublime.Region(0,view.size()))


    @classmethod
    def pkgpath(cls):
        return os.path.dirname(__file__)


    @classmethod
    def result_entry(cls, view):
        pass


    @classmethod
    def result_fileloc(cls, view):
        pass


def is_btlime_info(veiw):
    return view.match_selector(current.point(view), "btlime.info")


def get_line(view, point):
    '''
    Get the line from view:point
    @returns:
        (line_content, line_region, line_left_point)
        note that, the line_content dose not contains newline character, but
            the line_region contains
    '''
    region = view.full_line(point)
    content = view.substr(region)

    return content.rstrip("\n"), region, region.a


def _match_line_number(line):
    line_number_pattern = re.compile(r"^(\d+)[-:]")
    match = line_number_pattern.match(line)
  
    return int(match.group(1)) if match else None

def _match_file_name(line):
    file_name_pattern = re.compile(r"^@(.+)")
    match = file_name_pattern.match(line)

    return match.group(1) if match else None


def get_file_location(view, point):
    '''
    Get the file location from the btlime info entry.
        For example:
            @/aaa/bbb/xxx.py
            23- for i in range(100)
            24:     i = i**2
            25-     print i
        will get the file location: /aaa/bbb/xxx.py:24
    '''
    line_content, _, line_point = get_line(view, point)

    file_name = _match_file_name(line_content)
    if file_name:
        return "{0}:{1}".format(file_name, 0)

    lineno = _match_line_number(line_content)
    if not lineno:
        return None

    current_point = line_point-1
    while current_point >= 0:
        line_content, _, line_point = get_line(view, current_point)

        file_name = _match_file_name(line_content)
        if not file_name:
            current_point = line_point-1
            print(current_point, line_content)
            continue
        else:
            return "{0}:{1}".format(file_name, lineno)


def get_info_entry(veiw, point):
    '''
    Get the btlime info entry from the btlime info entry.
    @returns:
        The entry string, For example:
            <Match:i**2>
            @/aaa/bbb/xxx.py
            23- for i in range(100)
            24:     i = i**2
            25-     print i
        will get the file location: /aaa/bbb/xxx.py:24
    '''
    result = ""
    line_content, line_region, line_point = get_line(view, point)

    before = []
    current_point = line_point - 1
    while current_point >= 0:
        current_content, _, current_point = get_line(view, current_point)
        # if meet blank line break
        if not current_point:
            break

        before.insert(0, current_content)

    before_point = current_point

    after = []
    current_point = line_point + 1
    while current_point < view.size():
        current_content, current_region, current_point = \
            get_line(view, current_point)
        # if meet blank line break
        if not current_point:
            break

        after.append(current_content)

    after_point = current_region.b + 1

    result = "\n".join(before) + (line_content+"\n") + "\n".join(after)

    return result, Region(before_point, after_point)



def get_code_context(view, point, ctxs=2):
    row = lambda p: view.rowcol(p)[0]

    line_content, line_region, line_point = get_line(view, point)

    word = view.word(point)
    rowno = row(line_point)
    context = [(rowno, line_content)]

    for i in range(ctxs):
        current_point = line_point - 1
        current_content, _, current_point = get_line(view, current_point)
        context.insert(0, (row(current_point), current_content))

    for i in range(ctxs):
        current_point = current_region.b + 1
        current_content, current_region, _ = get_line(view, current_point)
        context.append((row(current_point), current_content))

    return context, rowno, word


def get_formated_code_context(view, point, ctxs=2):
    context = get_code_context(view, point, ctxs)

    result = "<Match:{0}>\n".format(context[2])

    no_fmt = "{0:>" + str(len(str(largest_lineno))) + "}"
    fmt = "{lineno}{spliter} {content}\n"

    for line in context[0]:
        spliter = "-" if line[0]!=context[1] else ":"
        result = result + fmt.format(lineno = no_fmt(line[0]),
            spliter = spliter,
            content = line[1])

    return result + "\n"



def load_patterns(scope):
    if 'source.python' in scope:
        idfile = os.path.join(current.pkgpath(), 'issuedef', "python")
    elif 'source.java' in scope:
        idfile = os.path.join(current.pkgpath(), 'issuedef', "java")
    elif 'source.php' in scope:
        idfile = os.path.join(current.pkgpath(), 'issuedef', "php")
    else:
        idfile = None

    if idfile:
        config = YamlConf(idfile)
    else:
        return None

    patterns = []
    if config:
        default_patterns = config.get('default-patterns',[])
        user_patterns = config.get('user-patterns',[])
        if isinstance(default_patterns, list):
            for pattern in default_patterns:
                patterns.append(re.compile(pattern))

        if isinstance(user_patterns, list):
            for pattern in user_patterns:
                patterns.append(re.compile(pattern))

    return patterns



class SimpleAnalyzer(object):
    pass



class RunBugtrackCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        projdir = args['dirs'][0]

        settings = sublime.load_settings('btlime.sublime-settings')
        btcmd = settings.get("bugtrack_command", "bugtrack")
        cachedir = settings.get("cache_directory_name", ".btlime-cache")
        cachedir = os.path.join(projdir, cachedir)
        
        self._run_bugtrack(btcmd, projdir, cachedir)


    @run_in_thread
    def _run_bugtrack(self, btcmd, projdir, cachedir):
        projname = os.path.split(projdir)[-1]
        cachename = os.path.split(cachedir)[-1]
        result_file = os.path.join(cachedir, projname+".bugtrack")

        if not os.path.exists(cachedir):
            os.mkdir(cachedir)

        cmd = [btcmd, projdir, "--exclude", cachename,
            "-o", result_file]
        cmd = " ".join(cmd)

        self.show_message("Running bugtrack ...")

        try:
            output = subprocess.check_output(cmd, shell=True)
        except Exception as error:
            sublime.error_message(str(error))
            return

        self.show_message("Bugtrack scan finished.")

        self.view.window().open_file(result_file)


    def show_message(self, msg):
        self.view.window().status_message(str(msg))



class ConfigBugtrackCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return



class GlobalCodeSearchCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return


#=====



class JumpLocationCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        point = current.point(self.view)

        file_loc = get_file_location(self.view, point)
        if not file_loc:
            return None

        file_name = file_loc.split(":")[0]
        if os.path.exists(file_name):
            self.view.window().open_file(file_loc, sublime.ENCODED_POSITION)
        else:
            sublime.error_message("File '{0}'' doses not exists.".format(
                file_name))



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



    def _get_issue_regions(self):
        result = []

        scope = current.scope(self.view)
        patterns = load_patterns(scope)
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

