#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Kiwi, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import sys
import threading
import platform
import shutil
import ConfigParser

import yaml
from appdirs import AppDirs
from colorama import init, Fore, Style

from exception import FileError



def getEncode():
    return sys.stdout.encoding if sys.stdout.encoding else "utf-8"


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



class Out(object):
    '''
    Output colorized information to console
    '''
    init()

    _WIDTH = 80
    _LINECHAR = "-"

    ENCODING = getEncode()

    def __init__(self, title=None):
        '''
        @params:
            title: tile information
        '''
        self._title = title


    def init(self, title=None):
        if title: self._title = title
        
        self.raw(self._banner())
        self.yellow(u"[{0}]".format(self._title))
        self.raw(self._LINECHAR * self._WIDTH)


    @classmethod
    def tostr(cls, msg):
        if isinstance(msg, unicode):
            msg = msg.encode(cls.ENCODING)
        elif not isinstance(msg, str):
            msg = str(msg)


    @classmethod
    def colorize(cls, msg, color):
        '''
        get red string
        '''
        cls.tostr(msg)

        if color.lower() in ['red','yellow','blue','green']:
            cstr = getattr(Fore, color.upper())
            return cstr + msg + Style.RESET_ALL
        else:
            return msg


    @classmethod
    def R(cls, msg): return cls.colorize(msg, 'red')

    @classmethod
    def Y(cls, msg): return cls.colorize(msg, 'yellow')

    @classmethod
    def G(cls, msg): return cls.colorize(msg, 'green')

    @classmethod
    def B(cls, msg): return cls.colorize(msg, 'blue')


    @classmethod
    def out(cls, msg, color): print cls.colorize(msg, color)


    @classmethod
    def raw(cls, msg): cls.out(msg, 'raw')

    @classmethod
    def red(cls, msg): cls.out(msg, 'red')

    @classmethod
    def yellow(cls, msg): cls.out(msg, 'yellow')

    @classmethod
    def green(cls, msg): cls.out(msg, 'green')

    @classmethod
    def blue(cls, msg): cls.out(msg, 'blue')


    @classmethod
    def info(cls, msg): 
        print "[i]:", cls.colorize(msg, 'raw')

    @classmethod
    def error(cls, msg): 
        print cls.R("[e]:"), cls.R(msg)

    @classmethod
    def wraning(cls, msg): 
        print cls.Y("[w]:"), cls.Y(msg)

    @classmethod
    def success(cls, msg):
        print cls.G("[s]:"), cls.G(msg)


    def _banner(self):
        '''
        banner information
        '''
        fmt = "|{0:^" + str(self._WIDTH+7) + "}|"

        banner = "+" + self._LINECHAR * (self._WIDTH-2) + "+\n"
        banner = banner + fmt.format(self.Y("Kiwi.") + \
            " Security tool for auditing source code") + "\n"
        banner = banner + fmt.format(
            self.G("https://github.com/alpha1e0/kiwi")) + "\n"
        banner = banner + "+" + self._LINECHAR * (self._WIDTH-2) + "+\n"

        return banner


    def close(self):
        self.raw(self._LINECHAR * self._WIDTH)


    def __enter__(self):
        self.init()
        return self


    def __exit__(self, *args):
        self.close()



class Config(Dict):
    def init_args(self, args):
        for key in dir(args):
            if not key.startswith("_"):
                self[key] = getattr(args, key)

        data_path = self['feature_dir']
        data_path = data_path or os.getenv("KIWI_DATA_PATH")

        if not data_path:
            Out.error(u"未找到漏洞特征目录，请使用参数-f/--feature_dir，"
                u"或环境变量 KIWI_DATA_PATH 指定漏洞特征目录")
            exit(1)

        self['datapath'] = data_path

        self['featurepath'] = os.path.join(self['datapath'], "features")
        self['evalpath'] = os.path.join(self['featurepath'], "evals")
        self['mapfile'] = os.path.join(self['datapath'], "filemap")
        self['senfiles'] = os.path.join(self['datapath'], "senfiles")

        self['opengrok_base'] = os.getenv("KIWI_OPENGROK_BASE") or None

        self['pkgpath'] = os.path.dirname(os.path.dirname(
            os.path.realpath(__file__)))




conf = Config()

