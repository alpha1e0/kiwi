######################################################################
# Bugtrack, a sublime plugin for finding security bugs.
# Copyright (c) 2016 alpha1e0
#===================================================
# signature file for python
######################################################################


rules:
  PY_OS_INJECT_0001:
    type: 1
    pattern: "os.system"
    description: "os command execute"
    score: 8
    action: match
  PY_OS_INJECT_0002:
    type: 1
    pattern: "os.system"
    description: "os command execute"
    score: 8
    action: match

types:
  1: "os command execute"

version: 1.0