#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
-----------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import re

from libs.commons import FileError
from libs.commons import YamlConf
from libs.commons import getPluginPath



class FileWalker(list):
    '''
    FileWalker will walk the project directory to find all normal files.
        All the files informations will be recorded in the FileWalker object.
        The FileWalker object is a list, the list item is [filename, scope, indexes]
    '''
    METAINFOLEN = 1024

    def __init__(self, directory, meta=False):
        '''
        @param:
            meta: if mata is true, FileWalker will try to match the meta
                information of the file
        '''
        if not os.path.exists(directory):
            raise FileError("Analyzer cannot find directory '{0}'".format(directory))

        self.directory = directory
        self._meta = meta

        self._fileMapping = self._loadFileMappingCfg()
        self._fileIgnore = self._loadFileIgnoreCfg()

        self._fileWalk()

        super(FileWalker, self).__init__()


    def _loadFileMappingCfg(self):
        mappingFile = os.path.join(getPluginPath(), "data", "filemap")

        mappings = YamlConf(mappingFile)
        for extSig in mappings['extensions']:
            extSig['pattern'] = re.compile(extSig['pattern'])

        if self._meta:
            for metaSig in mappings['metainfos']:
                metaSig['pattern'] = re.compile(metaSig['pattern'])

        return mappings


    def _loadFileIgnoreCfg(self):
        ignoreCfgFile = os.path.join(getPluginPath(), "porject.settings")

        cfg = YamlConf(ignoreCfgFile)['ignores']

        return cfg


    def _isTextFile(self, fileName):
        status = os.fstat(fileName)
        if not stat.S_ISREG(status.st_mode):
            return False


    def _isIgnore(self, fileName):
        for d in self._fileIgnore['directories']:
            if "/"+d+"/" in fileName or fileName.endswiths("/"+d):
                return True

        for e in self._fileIgnore['extensions']:
            if fileName.endswiths("."+e):
                return True

        for f in self._fileIgnore["files"]:
            if fileName.endswiths("/"+f):
                return True

        return False


    def _getFileScope(self, fileName):
        '''
        get the file scope
        '''
        scope = None

        for extSig in self._fileMapping['extensions']:
            if extSig['pattern'].search(fileName):
                scope = extSig['scope']

        if scope is None and self._meta:
            with open(fileName) as _file:
                infoStr = _file.read(METAINFOLEN)
                for metaSig in self._fileMapping['metainfos']:
                    if metaSig['pattern'].search(infoStr):
                        scope = metaSig['scope']

        return scope if scope else "raw"


    def _fileWalk(self):
        for path, dirlist, filelist in os.walk(self.directory):
            for file in filelist:
                fileName = os.path.join(path,file)
                if self._isTextFile(fileName) and self._isIgnore(fileName):
                    scope = self._getFileScope(fileName)

                    self.append([fileName, scope, []])
