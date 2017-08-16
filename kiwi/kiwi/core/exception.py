#!/usr/bin/env python
#-*- coding:utf-8 -*-


'''
Kiwi, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''



class KiwiError(Exception):
    def __init__(self, msg, errno=0):
        self._msg = str(msg)
        self._errno = int(errno)


    def __str__(self):
        if self._errno:
            return "{} [{}]: {}".format(self.__class__.__name__, self._errno,
                self._msg)
        else:
            return "{}: {}".format(self.__class__.__name__, self._errno,
                self._msg)



class FileError(KiwiError):
    pass


class FeatureError(KiwiError):
    pass


class IssueFormatError(KiwiError):
    pass


class DatabaseError(KiwiError):
    pass