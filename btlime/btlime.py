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


BTLIME_SCOPE = 'btlime.info'
BTLIME_SETTING_FILE = 'btlime.sublime-settings'
BTLIME_SYNTAX_FILE = "Packages/btlime/btlime.sublime-syntax"
DEFAULT_ENCODING = "utf-8"



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



def run_in_thread(func):
    '''
    线程运行函数修饰器
    '''
    def thread_func(*args, **kwargs):
        def run():
            r = func(*args, **kwargs)

        t = threading.Thread(target=run)
        t.start()

    return thread_func



class current(object):
    '''
    current类，用于获取当前信息，例如：
        当前光标所在region
        当前光标的单词
    '''
    @classmethod
    def point(cls, view):
        '''
        获取当前view中光标所在偏移（相对于文本文件中第一个字符）
        '''
        return view.sel()[0].a


    @classmethod
    def region(cls, view):
        '''
        获取当前view的当前region信息（[start_index, end_index])
        '''
        return view.sel()[0]


    @classmethod
    def wordregion(cls, view):
        '''
        获取当前view选中的单词的region，或者当前view光标所在单词的region
        '''
        sel = view.sel()[0]
        if sel.a == sel.b:
            return view.word(sel)
        else:
            return sel


    @classmethod
    def regions(cls, view):
        '''
        获取当前view所有regions
        '''
        return [r for r in view.sel()]


    @classmethod
    def scope(cls, view):
        '''
        获取当前view的scope信息，例如：source.python
        '''
        return view.scope_name(view.sel()[0].a)


    @classmethod
    def word(cls, view):
        '''
        获取当前选中的单词
        '''
        return view.substr(cls.wordregion(view))


    @classmethod
    def rowcol(cls, view):
        point = view.sel()[0].a
        return view.rowcol(point)


    @classmethod
    def projdir(cls, view):
        '''
        获取当前文件所在的forder
        '''
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
    def cache_dir(cls, view):
        '''
        获取临时文件、缓存文件保存的目录
        '''
        settings = sublime.load_settings(BTLIME_SETTING_FILE)
        cachedir = settings.get("cache_directory_name", ".btlime-cache")
        projdir = cls.projdir(view)

        return os.path.join(projdir, cachedir)


    @classmethod
    def review_file(cls, view):
        '''
        获取review_file
        '''
        projdir = cls.projdir(view)

        return CacheFile(projdir, 'review')


    @classmethod
    def trace_file(cls, view):
        '''
        获取trace_file
        '''
        projdir = cls.projdir(view)

        return CacheFile(projdir, 'trace')


    @classmethod
    def trash_file(cls, view):
        '''
        获取trash_file
        '''
        projdir = cls.projdir(view)

        return CacheFile(projdir, 'trash')



def show_error(msg):
    '''
    弹窗显示错误信息
    '''
    sublime.error_message(str(msg))


def show_status(msg):
    '''
    状态栏显示信息
    '''
    sublime.active_window().status_message(str(msg))


def is_btlime_info(view):
    '''
    判断是否为scope=btlime.info
    '''
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
    if not line_content:
        return None, None

    file_name = _match_file_name(line_content)
    if file_name:
        return file_name, 0

    lineno = _match_line_number(line_content)
    if not lineno:
        return None, None

    current_point = line_point-1
    while current_point >= 0:
        line_content, _, line_point = get_line(view, current_point)

        file_name = _match_file_name(line_content)
        if not file_name:
            current_point = line_point-1
            continue
        else:
            return file_name, lineno


def get_info_entry(view, point):
    '''
    Get the btlime info entry from the btlime info entry.
    @returns:
        The entry string, For example:
            <Match:i**2>
            @/aaa/bbb/xxx.py
            23- for i in range(100)
            24:     i = i**2
            25-     print i
    '''
    result = ""
    line_content, line_region, line_point = get_line(view, point)

    if not line_content:
        return line_content, line_region

    before = []
    current_point = line_point - 1
    while current_point >= 0:
        current_content, _, current_point = get_line(view, current_point)
        # if meet blank line break
        if not current_content:
            break

        before.insert(0, current_content)
        current_point = current_point-1

    before_point = current_point+1

    after = []
    current_point = line_region.b
    while current_point < view.size():
        current_content, current_region, current_point = \
            get_line(view, current_point)
        # if meet blank line break
        if not current_content:
            break

        after.append(current_content)
        current_point = current_region.b

    after_point = current_region.b

    result = "\n".join(before) + "\n" + (line_content+"\n") + "\n".join(after)

    return result, sublime.Region(before_point, after_point)


def get_projdir_from_entry(view, point):
    file_name, _ = get_file_location(view, point)
    if not file_name:
        return None

    for folder in view.window().folders():
        if file_name.startswith(folder):
            return folder

    return None


def get_code_context(view, point, ctxs=2):
    row = lambda p: view.rowcol(p)[0]+1

    line_content, line_region, line_point = get_line(view, point)

    word = current.word(view)
    rowno = row(line_point)
    context = [(rowno, line_content)]

    current_point = line_point
    for i in range(ctxs):
        current_point = current_point - 1
        current_content, _, current_point = get_line(view, current_point)
        context.insert(0, (row(current_point), current_content))

    current_region = line_region
    for i in range(ctxs):
        current_point = current_region.b + 1
        current_content, current_region, _ = get_line(view, current_point)
        context.append((row(current_point), current_content))

    return context, rowno, word


def get_formated_code_context(view, point, ctxs=2):
    context, rowno, word = get_code_context(view, point, ctxs)
    largest_lineno = context[-1][0]

    result = "<Match:{0}>\n@{1}\n".format(word, view.file_name())

    no_fmt = "{0:>" + str(len(str(largest_lineno))) + "}"
    fmt = "{lineno}{spliter} {content}\n"

    for line in context:
        spliter = "-" if line[0]!=rowno else ":"
        result = result + fmt.format(lineno = no_fmt.format(line[0]),
            spliter = spliter,
            content = line[1])

    return result + "\n"



def load_patterns(scope):
    settings = sublime.load_settings(BTLIME_SETTING_FILE)
    issuedef = settings.get("issuedef", None)
    if not issuedef:
        return []

    for entry in issuedef:
        if entry['scope'] in scope:
            idfile = os.path.join(current.pkgpath(), 'issuedef', 
                entry['filename'])
            break
    else:
        idfile = None

    if idfile:
        config = YamlConf(idfile)
    else:
        return []

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


def run_cmd(cmd):
    if isinstance(cmd, list):
        cmd = [str(c) for c in cmd]

    output = ""
    shell = True if sublime.platform() == 'windows' else False
    try:
        output = subprocess.check_output(cmd, shell=shell)
    except Exception as error:
        show_error(str(error))

    return output


def search(patterns, directories, includes, excludes):
    settings = sublime.load_settings(BTLIME_SETTING_FILE)
    ptcmd = settings.get("code_search_command")

    if ptcmd:
        return pt_search(ptcmd, patterns, directories, includes, excludes)
    else:
        return simple_search(patterns, directories, includes, exculdes)


def _build_pt_command(ptcmd, pattern, directory, ctxs):
    if sublime.platform() == 'windows':
        ctxs_lable = "/C"
    else:
        ctxs_lable = "-C"

    return [ptcmd, pattern, directory, ctxs_lable, ctxs]


def _format_pt_result(ptresult, pattern):
    result = ""

    entry = ""
    current_file = ""

    line_pattern = re.compile(r"^(.+):(\d+[:-])(.*)$")

    if isinstance(ptresult, bytes):
        lines = ptresult.decode().split("\n")
    else:
        lines = ptresult.split("\n")
        
    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = line_pattern.match(line)
        if not match:
            continue

        filename, lineno, content = match.group(1), \
            match.group(2), " {0}".format(match.group(3))

        if current_file != filename:
            current_file = filename
            result = result + "\n" + entry
            entry = "<Match:{0}>\n".format(pattern)
            entry = entry + "@{0}\n".format(current_file)

        entry = entry + lineno + content + "\n"

    result = result + "\n" + entry

    return result



def pt_search(ptcmd, patterns, directories, includes, excludes):
    settings = sublime.load_settings(BTLIME_SETTING_FILE)
    ctxs = settings.get("result_context", 2)

    search_result = ""
    for pattern in patterns:
        for directory in directories:
            cmd = _build_pt_command(ptcmd, pattern, directory, ctxs)
            pt_output = run_cmd(cmd)
            search_result = search_result + "\n" + _format_pt_result(pt_output,
                pattern)

    return "#!btlime" + search_result



def simple_search(patterns, directories, includes, exculdes):
    show_error("Can not find code search tool 'pt',"
        " and simple mode is not support now")


class CacheFile(object):
    def __init__(self, projdir, cachetype):
        '''
        manage class for cache-file
        @params:
            projdir: the project directory
            cachetype: cache-file type, should be one of 
                ['review','trace','trash']
        '''
        if cachetype not in ['review','trace','trash']:
            raise FileError("cache-file type error.")

        self._header = "#!btlime\n\n## This is the view for {0}\n\n".format(
            cachetype)

        settings = sublime.load_settings(BTLIME_SETTING_FILE)
        cachedir = settings.get('cache_directory_name', ".btlime-cache")
        self._cachepath = os.path.join(projdir, cachedir)
        if not os.path.exists(self._cachepath):
            os.makedirs(self._cachepath)

        self._cachefile = os.path.join(self._cachepath, cachetype)
        if not os.path.exists(self._cachefile):
            with open(self._cachefile, "w") as _file:
                _file.write(self._header)


    def append(self, data):
        with open(self._cachefile, "a", encoding=DEFAULT_ENCODING) as _file:
            _file.write(str(data))




def analyze(view, btcmd, projdir, cachedir):
    if btcmd:
        bt_analyze(view, btcmd, projdir, cachedir)
    else:
        simple_analyze(view, projdir, cachedir)



@run_in_thread
def bt_analyze(view, btcmd, projdir, cachedir):
    projname = os.path.split(projdir)[-1]
    cachename = os.path.split(cachedir)[-1]
    result_file = os.path.join(cachedir, projname+".bugtrack")

    if not os.path.exists(cachedir):
        os.mkdir(cachedir)

    cmd = [btcmd, projdir, "--exclude", cachename,
        "-o", result_file]
    cmd = " ".join(cmd)

    show_status("Running bugtrack ...")

    shell = True
    try:
        output = subprocess.check_output(cmd, shell=shell)
    except Exception as error:
        show_error(str(error))
        return

    show_status("Bugtrack scan finished.")

    view.window().open_file(result_file)


@run_in_thread
def simple_analyze(view, projdir, cachedir):
    show_error("Can not find code search tool 'bugtrack',"
        " and simple mode is not support now")



class RunBugtrackCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        projdir = args['dirs'][0]

        settings = sublime.load_settings(BTLIME_SETTING_FILE)
        btcmd = settings.get("bugtrack_command", None)

        cachedir = settings.get("cache_directory_name", ".btlime-cache")
        cachedir = os.path.join(projdir, cachedir)
        
        analyze(self.view, btcmd, projdir, cachedir)




class GlobalCodeSearchCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return


#=====



class JumpLocationCommand(sublime_plugin.TextCommand):
    @property
    def _is_btlime_view(self):
        scope_name = self.view.scope_name(0)
        return True if BTLIME_SCOPE in scope_name else False

    def run(self, edit, **args):
        if not self._is_btlime_view:
            return

        point = current.point(self.view)

        file_name, lineno = get_file_location(self.view, point)
        if not file_name:
            return None

        if os.path.exists(file_name):
            file_loc = "{0}:{1}".format(file_name, lineno)
            self.view.window().open_file(file_loc, sublime.ENCODED_POSITION)
        else:
            show_error("File '{0}'' doses not exists.".format(
                file_name))



class SendtoTrashCommand(sublime_plugin.TextCommand):
    @property
    def _is_btlime_view(self):
        scope_name = self.view.scope_name(0)
        return True if BTLIME_SCOPE in scope_name else False

    def run(self, edit, **args):
        if not self._is_btlime_view:
            return

        content, region = get_info_entry(self.view, current.point(self.view))
        if not content:
            return

        try:
            trash_file = current.trash_file(self.view)
        except AttributeError:
            projdir = get_projdir_from_entry(self.view, 
                current.point(self.view))
            if not projdir:
                return
            trash_file = CacheFile(projdir, "trash")

        trash_file.append("\n"+content+"\n")

        self.view.erase(edit, region)



class SendtoReviewCommand(sublime_plugin.TextCommand):
    @property
    def _is_btlime_view(self):
        scope_name = self.view.scope_name(0)
        return True if BTLIME_SCOPE in scope_name else False

    def run(self, edit, **args):
        if not self._is_btlime_view:
            return

        content, region = get_info_entry(self.view, 
            current.point(self.view))
        if not content:
            return

        try:
            review_file = current.review_file(self.view)
        except AttributeError:
            projdir = get_projdir_from_entry(self.view, 
                current.point(self.view))
            if not projdir:
                return
            review_file = CacheFile(projdir, 'review')

        review_file.append("\n"+content+"\n")




class ShowIssueCommand(sublime_plugin.TextCommand):
    ISSUE_KEY = "btlime-issue"
    ISSUES_COPE = "invalid.illegal"

    def __init__(self, *args, **kwargs):
        self._current_region_index = 0
        self._issue_regions = []

        super(ShowIssueCommand, self).__init__(*args, **kwargs)


    def run(self, edit, **args):
        if not self._is_showing:
            self._issue_regions = self._get_issue_regions()

            self.view.add_regions(self.ISSUE_KEY, self._issue_regions, 
                self.ISSUES_COPE)

            self.view.show(self._issue_regions[0])
            self.view.settings().set("is_finding", True)
        else:
            region = self._get_next_region()
            self.view.show(region)


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


    def _get_next_region(self):
        index = self._current_region_index + 1
        if index == len(self._issue_regions):
            index = 0

        self._current_region_index = index
        return self._issue_regions[index]


    @property
    def _is_showing(self):
        return True if self.view.get_regions(self.ISSUE_KEY) else False


class FindAllCommand(sublime_plugin.TextCommand):
    FINDING_KEY = "finding"
    FINDING_SCOPE = "invalid.deprecated"

    def __init__(self, *args, **kwargs):
        self._current_region_index = 0
        self._match_regions = []

        super(FindAllCommand, self).__init__(*args, **kwargs)


    def run(self, edit, **args):
        forward = args.get('forward', False)

        if not self._is_current_finding:
            self.view.erase_regions(self.FINDING_KEY)
            self.view.settings().set("is_finding", False)

            current_region = current.wordregion(self.view)
            match_word = current.word(self.view)

            self._match_regions, self._current_region_index = \
                self._get_match_info(current_region, match_word)
            self._draw_regions(self._match_regions)

            self.view.settings().set("is_finding", True)
        else:
            if forward:
                region = self._get_pre_region()
            else:
                region = self._get_next_region()

            self.view.show(region)


    def _get_match_info(self, current_region, match_word):
        '''
        获取所有匹配位置
        '''
        index = 0
        all_match_regions = self.view.find_all(match_word, sublime.LITERAL)

        for region in all_match_regions:
            if region == current_region:
                break
            index += 1

        if index >= len(all_match_regions):
            index = len(all_match_regions)

        return all_match_regions, index


    def _get_pre_region(self):
        index = self._current_region_index - 1
        if index == -1:
            index = len(self._match_regions) - 1

        self._current_region_index = index
        return self._match_regions[index]


    def _get_next_region(self):
        index = self._current_region_index + 1
        if index == len(self._match_regions):
            index = 0

        self._current_region_index = index
        return self._match_regions[index]


    def _draw_regions(self, regions):
        self.view.add_regions(self.FINDING_KEY, regions, self.FINDING_SCOPE)


    @property
    def _is_current_finding(self):
        regions = self.view.get_regions(self.FINDING_KEY)
        
        if regions:
            return True
        
        return False



class FindFirstCommand(sublime_plugin.TextCommand):
    FINDING_KEY = "finding"
    FINDING_SCOPE = "invalid.deprecated"

    def run(self, edit, **args):
        if not self._is_current_finding:
            self.view.erase_regions(self.FINDING_KEY)
            self.view.settings().set("is_finding", False)
            
            current_region = current.wordregion(self.view)
            current_word = current.word(self.view)
            first_region = self.view.find(current_word, 0, sublime.LITERAL)

            self._draw_regions([current_region, first_region])
            
            self.view.settings().set("is_finding", True)
            self.view.show(first_region)

            return

        visible_region = self.view.visible_region()
        for region in self._match_regions:
            if not visible_region.contains(region):
                self.view.show(region)
                return


    def _draw_regions(self, regions):
        self.view.add_regions(self.FINDING_KEY, regions, self.FINDING_SCOPE)


    @property
    def _match_regions(self):
        return self.view.get_regions(self.FINDING_KEY)


    @property
    def _is_current_finding(self):
        regions = self.view.get_regions(self.FINDING_KEY)
        
        if regions:
            return True
        
        return False



class CleanFindingsCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        self.view.erase_regions(FindAllCommand.FINDING_KEY)
        self.view.erase_regions(ShowIssueCommand.ISSUE_KEY)
        self.view.settings().set("is_finding", False)



class RecordtoTraceCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        settings = sublime.load_settings(BTLIME_SETTING_FILE)
        ctxs = settings.get("result_context", 2)

        context = get_formated_code_context(self.view, 
            current.point(self.view),ctxs)
        
        trace_file = current.trace_file(self.view)
        trace_file.append("\n"+context+"\n")



class RecordtoReviewCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        settings = sublime.load_settings(BTLIME_SETTING_FILE)
        ctxs = settings.get("result_context", 2)

        context = get_formated_code_context(self.view, 
            current.point(self.view),ctxs)
        
        review_file = current.review_file(self.view)
        review_file.append("\n"+context+"\n")



class CodeSearchCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        word = current.word(self.view)
        directory = current.projdir(self.view)

        search_result = search([word], [directory], None, None)

        view = self.view.window().new_file()
        view.insert(edit, 0, search_result)
        view.set_name("search {0}".format(word))
        view.set_syntax_file(BTLIME_SYNTAX_FILE)



class GotoDefinationCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        return


class OpenIssueDefCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        settings = sublime.load_settings(BTLIME_SETTING_FILE)
        issuedef = settings.get("issuedef", None)
        if not issuedef:
            return

        for entry in issuedef:
            idfile = os.path.join(current.pkgpath(), 'issuedef', 
                entry['filename'])
            self.view.window().open_file(idfile)
