#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
-----------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os

try:
    from libs.commons import FileError, loadFileMappingCfg
except ImportError:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    from libs.commons import FileError, loadFileMappingCfg



class FileSet(object):
    def __init__(self, path):
        if not os.path.exit(path):
            raise FileError("cannot find path '{0}'".format(path))
        else:
            self._path = path

        self._fileMapping = loadFileMappingCfg()

        self.fileSet = self._build


    def _getFileType(self, fileName):
        '''
        use fileName to generate file entry
        '''
        extPos = fileName.rfind(".")
        if extPos == -1:
            return "raw", fileName
        else:
            ext = fileName[extPos:]
            if ext in self._fileMapping:
                return self._fileMapping[ext], fileName
            else:
                return "raw", fileName


    def _build(self):
        fileSet = {}

        for path, dirlist, filelist in os.walk(self._path):
            for file in filelist:
                fileName = os.path.join(path,file)
                fileType = self._getFileType(fileName)
                if fileType not in fileSet:
                    fileSet[fileType] = []

                fileSet[fileType].append(fileName)

        return fileSet


    def doAnalyse(self):
        pass


