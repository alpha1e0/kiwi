#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
-----------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''



class BugtrackError(Exception):
    def __init__(self, msg):
        self._msg = str(msg)


    def __str__(self):
        return self._msg



class FileError(BugtrackError):
    def __str__(self):
        return "File error " + self._msg