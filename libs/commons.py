#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
-----------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import functools
import threading

import yaml



PULGIN_NAME = "bugtrack"


class BaseError(Exception):
    def __init__(self, msg):
        self._msg = str(msg)


    def __str__(self):
        return self._msg



class FileError(BaseError):
    def __str__(self):
        return "File error " + self._msg



def getPluginPath():
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))



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



class CacheManage(object):
    def __init__(self, projPath, cacheDirName):
        if not os.path.exists(projPath):
            raise FileError("project path '{0}' dose not exists".format(projPath))
        else:
            self._projPath = projPath

        self._cachePath = os.path.join(projPath, cacheDirName)
        if not os.path.exists(self._cachePath):
            os.mkdir(self._cachePath)


    def addFile(self, name, content):
        cacheFileName = os.path.join(self._cachePath, name)

        with open(cacheFileName, 'w', encoding='utf-8') as _file:
            _file.write(content)



def runInThread(func):
    @functools.wraps(func)
    def threadFunc(*args, **kwargs):
        def run():
            r = func(*args, **kwargs)

        t = threading.Thread(target=run)
        t.start()

    return threadFunc


