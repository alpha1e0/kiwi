#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
-----------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import functools
import threading
import platform
import shutil
import ConfigParser

import yaml
import appdirs

from exceptions import FileError


class YamlConf(object):
    '''
    Yaml configure file loader
    '''
    def __new__(cls, path):
        try:
            _file = open(path,"r")
            result = yaml.load(_file)
        except IOError:
            raise FileError("Loading yaml file '{0}' failed, read file failed".format(path))
        except yaml.YAMLError as error:
            raise FileError("Loading yaml file '{0}' failed, yaml error, reason: '{1}'".format(path,str(error)))
        except Exception as error:
            raise FileError("Loading yaml file '{0}' failed, reason: {1}".format(path,str(error)))

        return result



def runInThread(func):
    @functools.wraps(func)
    def threadFunc(*args, **kwargs):
        def run():
            r = func(*args, **kwargs)

        t = threading.Thread(target=run)
        t.start()

    return threadFunc



class Dict(dict):
    def __init__(self, **kwargs):
        super(Dict, self).__init__(**kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None

    def __setattr__(self, key, value):
        self[key] = value



class Output(object):
    '''
    终端输出功能
        该类用于输出信息到控制台和文件
    '''
    _RED = '\033[31m'
    _BLUE = '\033[34m'
    _YELLOW = '\033[33m'
    _GREEN = '\033[32m'
    _EOF = '\033[0m'

    _WIDTH = 80
    _CHAR = "-"

    def __init__(self, title=None, tofile=None):
        '''
        @params:
            title: 输出的标题
            tofile: 输出文件
        '''
        self._title = title
        self._fileName = tofile
        self._file = self._openFile(tofile)


    def _openFile(self, filename):
        if filename:
            try:
                _file = open(filename, "w")
            except IOError:
                _file = None
                raise PenError("open output file '{0}' failed".format(filename))
        else:
            _file = None

        return _file


    def openFile(self, filename):
        self._fileName = filename
        self._file = self._openFile(filename)


    def init(self, title=None, tofile=None):
        if title: self._title = title
        if tofile: 
            self._fileName = tofile
            self._file = self._openFile(tofile)
        
        self.raw(self._banner())
        self.yellow(u"[{0}]".format(self._title))
        self.raw(self._CHAR * self._WIDTH)


    @classmethod
    def safeEncode(cls, msg, method=None):
        '''
        安全编码
            如果msg中有不能编码的字节，自动处理为16进制
        '''
        if isinstance(msg, str):
            return msg
        elif isinstance(msg, unicode):
            method = method.lower() if method else sys.stdin.encoding
            try:
                return msg.encode(method)
            except UnicodeError:
                resultList = []
                for word in msg:
                    try:
                        encodedWord = word.encode(method)
                    except UnicodeError:
                        encodedWord = "\\x" + repr(word)[4:6] + "\\x" + repr(word)[6:8]

                    resultList.append(encodedWord)

                return "".join(resultList)
        else:
            try:
                msg = unicode(msg)
            except UnicodeDecodeError:
                msg = str(msg)
            return cls.safeEncode(msg,method)



    @classmethod
    def R(cls, msg):
        '''
        字符串着色为红色
        '''
        return cls._RED + msg + cls._EOF

    @classmethod
    def Y(cls, msg):
        '''
        字符串着色为橙色
        '''
        return cls._YELLOW + msg + cls._EOF

    @classmethod
    def B(cls, msg):
        '''
        字符串着色为蓝色
        '''
        return cls._BLUE + msg + cls._EOF

    @classmethod
    def G(cls, msg):
        '''
        字符串着色为绿色
        '''
        return cls._GREEN + msg + cls._EOF


    @classmethod
    def raw(cls, msg):
        '''
        无颜色输出
        '''
        print cls.safeEncode(msg)
    

    @classmethod
    def red(cls, msg):
        '''
        打印红色信息
        '''
        cls.raw(cls.R(msg))

    @classmethod
    def yellow(cls, msg):
        '''
        打印橙色信息
        '''
        cls.raw(cls.Y(msg))

    @classmethod
    def blue(cls, msg):
        '''
        打印蓝色信息
        '''
        cls.raw(cls.B(msg))

    @classmethod
    def green(cls, msg):
        '''
        打印绿色信息
        '''
        cls.raw(cls.G(msg))


    @classmethod
    def info(cls, msg):
        cls.raw(msg)

    @classmethod
    def error(cls, msg):
        cls.red(msg)

    @classmethod
    def warnning(cls, msg):
        cls.yellow(msg)


    def write(self, data):
        '''
        写入数据到文件
        '''
        if self._file:
            try:
                self._file.write(data)
                return True
            except IOError:
                raise PenError("write output file '{0}' failed".format(self._fileName))
        else:
            return False


    def writeLine(self, line, parser=None):
        '''
        写入一行数据到文件
        @params:
            line: 待写入的数据
            parser: 处理待写入数据的回调函数
        '''
        if self._file:
            if parser and isinstance(parser, types.FunctionType):
                line = parser(line)
            try:
                self._file.write(line + "\n")
                return True
            except IOError:
                raise PenError("write output file '{0}' failed".format(self._fileName))
        else:
            return False


    def _banner(self):
        '''
        生成banner信息
        '''
        fmt = "|{0:^" + "{0}".format(self._WIDTH+7) + "}|"

        banner = "+" + self._CHAR * (self._WIDTH-2) + "+\n"
        banner = banner + fmt.format(self.Y("PentestDB.") + " Tools and Resources for Web Penetration Test.") + "\n"
        banner = banner + fmt.format(self.G("https://github.com/alpha1e0/pentestdb")) + "\n"
        banner = banner + "+" + self._CHAR * (self._WIDTH-2) + "+\n"

        return banner


    def close(self):
        self.raw(self._CHAR * self._WIDTH)
        if self._file:
            self._file.close()


    def __enter__(self):
        self.init()
        return self


    def __exit__(self, *args):
        self.close()



class Log(object):
    '''
    Log class
        support:critical, error, warning, info, debug, notset
    Params:
        logname: specify the logname
        toConsole: whether outputing to console
        tofile: whether to logging to file
    '''
    def __new__(cls, logname=None, toConsole=True, tofile="pen"):
        logname = logname if logname else "pen"

        log = logging.getLogger(logname)
        log.setLevel(logging.DEBUG)

        if toConsole:
            streamHD = logging.StreamHandler()
            streamHD.setLevel(logging.DEBUG)
            formatter = logging.Formatter('[%(asctime)s] <%(levelname)s> %(message)s' ,datefmt="%Y-%m-%d %H:%M:%S")
            streamHD.setFormatter(formatter)
            log.addHandler(streamHD)

        if tofile:
            fileName = os.path.join(sys.path[0],"script","log",'{0}.log'.format(tofile))
            try:
                if not os.path.exists(fileName):
                    with open(fileName,"w") as fd:
                        fd.write("{0} log start----------------\r\n".format(tofile))
            except IOError:
                raise PenError("Creating log file '{0}' failed".format(fileName))
            fileHD = logging.FileHandler(fileName)
            fileHD.setLevel(logging.DEBUG)
            formatter = logging.Formatter('[%(asctime)s] <%(levelname)s> %(message)s' ,datefmt="%Y-%m-%d %H:%M:%S")
            fileHD.setFormatter(formatter)
            log.addHandler(fileHD)

        return log



class Config(Dict):
    def __init__(self):
        self['dirs'] = Dirs()

        confFile = os.path.join(self['dirs']['homePath'], "config")
        if not os.path.exists(confFile):
            sampleConfFile = os.path.join(self['dirs']['pkgPath'],"data","config.sample")
            if not os.path.exists(sampleConfFile):
                raise WIPError("cannot find configure file, 'config' or 'config.sample'")
            shutil.copy(sampleConfFile, confFile)

        cf = ConfigParser.ConfigParser()
        cf.read(confFile)

        for sec in cf.sections():
            self[sec] = Dict()
            for opt in cf.options(sec):
                self[sec][opt] = cf.get(sec, opt)



class Dirs(Dict):
    def __init__(self):
        homePath = None
        if 'Windows' not in platform.system():
            homePath = os.environ.get("HOME",None)
            if homePath is not None:
                homePath = os.path.join(homePath, ".bugtrack")
            
        if not homePath:
            homePath = appdirs.user_data_dir("bugtrack")

        if not os.path.exists(homePath):
            os.makedirs(homePath)

        sigsPath = os.path.join(homePath, "sigs")
        logPath = os.path.join(homePath, "log")

        for d in [sigsPath, logPath]:
            if os.path.exists(d):
                os.makedirs(d)

        self['homePath'] = homePath
        self['sigsPath'] = sigsPath
        self['logPath'] = logPath
        self['pkgPath'] = os.path.dirname(os.path.dirname(__file__))



conf = Config()












