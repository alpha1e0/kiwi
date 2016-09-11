#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
-----------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os

try:
    from libs.commons import FileError, loadFileMappingCfg
    import engines
except ImportError:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    from libs.commons import FileError, loadFileMappingCfg



class FileSet(object):
    def __init__(self, directory):
        if not os.path.exit(directory):
            raise FileError("FileSet cannot find directory '{0}'".format(directory))

        self.directory = directory

        self._fileMapping = loadFileMappingCfg()

        self._fileSet = self._build()


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

        for path, dirlist, filelist in os.walk(self.directory):
            for file in filelist:
                fileName = os.path.join(path,file)
                fileType = self._getFileType(fileName)
                if fileType not in fileSet:
                    fileSet[fileType] = []

                fileSet[fileType].append(SourceFile(fileType, fileName))

        return fileSet


    def doAnalyse(self):
        '''
        @returns:
            {type, filenames, matchs}
        '''
        result = {}

        for ftype, files in self._fileSet.iteritems():
            result[ftype] = {}
            for sf in files:
                r = sf.doAnalyse()
                result[ftype][sf.fileName] = r

        return result
                

    def export(self, data):
        pass


class SourceFile(object):
    def __init__(self, fileType, fileName):
        if not os.path.exit(fileName):
            raise FileError("Source File can not find file {0}".format(fileName))

        self.fileName = fileName
        self.fileType = fileType


    def _loadEngine(self):
        for member in dir(engines):
            if member.lower().startswith(self.fileType):
                engineClass = getattr(engines, member)
        else:
            engineClass = engines.Engine

        return enginesClass


    def doAnalyse(self):
        engine = self._loadEngine()()

        with open(self.fileName) as _file:
            content = _file.read()

        return engine.search(content)

