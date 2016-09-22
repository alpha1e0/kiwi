#===============================================================================
# Bugtrack, a sublime plugin for finding security bugs.
# Copyright (c) 2016 alpha1e0
# -----------------------------------------------------------------------------
# Sensitive information leaking
#===============================================================================

version: 1.0

engine: GrepEngine

scopes: 
  - python

rules:
  - SI-0001:
      severity: High
      confidence: High
      information: "Password information leaking"
      references: []
      patterns:
        - password
