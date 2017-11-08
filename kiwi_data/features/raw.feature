%YAML 1.2
---

#===============================================================================
# Kiwi, Security tool for auditing source code
# Copyright (c) 2016 alpha1e0
# -----------------------------------------------------------------------------
# Sensitive information leaking
#===============================================================================

version: 1.0

engine: GrepEngine

scopes:
  - raw

features:
- ID: RAW_PASSWD_INFO_001
  name: "Password information leaking"
  severity: High
  confidence: High
  references: []
  patterns:
    - password
