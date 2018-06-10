%YAML 1.2
---

#===============================================================================
# Kiwi, Security tool for auditing source code
# Copyright (c) 2016 alpha1e0
# -----------------------------------------------------------------------------
# Issue defines for php
#===============================================================================

version: 1.0

scopes: 
  - php


features:
- ID: PHP_CMD_INJ_001
  name: "Execute command in shells"
  references: []
  severity: High
  confidence: Medium
  patterns:
    - \bbackticks\s*\(
    - \bexec\s*\(
    - \bexpect_popen\s*\(
    - \bpassthru\s*\(
    - \bpcntl_exec\s*\(
    - \bpopen\s*\(
    - \bproc_open\s*\(
    - \bshell_exec\s*\(
    - \bsystem\s*\(
    - \bw32api_invoke_function\s*\(
    - \bw32api_register_function\s*\(
    #- \bmail\s*\(
    - \bmb_send_mail\s*\(


- ID: PHP_SQL_INJ_002
  name: "Execute SQL command inject"
  severity: High
  confidence: Medium
  references: []
  patterns:
    - \bdba_open\s*\(
    - \bdba_popen\s*\(
    - \bdba_insert\s*\(
    - \bdba_fetch\s*\(
    - \bdba_delete\s*\(
    - \bdbx_query\s*\(
    - \bodbc_do\s*\(
    - \bodbc_exec\s*\(
    - \bodbc_execute\s*\(
    - \bdb2_exec\s*\(
    - \bdb2_execute\s*\(
    - \bfbsql_db_query\s*\(
    - \bfbsql_query\s*\(
    - \bibase_query\s*\(
    - \bibase_execute\s*\(
    - \bifx_query\s*\(
    - \bifx_do\s*\(
    - \bingres_query\s*\(
    - \bingres_execute\s*\(
    - \bingres_unbuffered_query\s*\(
    - \bmsql_db_query\s*\(
    - \bmsql_query\s*\(
    - \bmsql\s*\(
    - \bmssql_query\s*\(
    - \bmssql_execute\s*\(
    - \bmysql_db_query\s*\(
    - \bmysql_query\s*\(
    - \bmysql_unbuffered_query\s*\(
    - \bmysqli_stmt_execute\s*\(
    - \bmysqli_query\s*\(
    - \bmysqli_real_query\s*\(
    - \bmysqli_master_query\s*\(
    - \boci_execute\s*\(
    - \bociexecute\s*\(
    - \bovrimos_exec\s*\(
    - \bovrimos_execute\s*\(
    - \bora_do\s*\(
    - \bora_exec\s*\(
    - \bpg_query\s*\(
    - \bpg_send_query\s*\(
    - \bpg_send_query_params\s*\(
    - \bpg_send_prepare\s*\(
    - \bpg_prepare\s*\(
    - \bsqlite_open\s*\(
    - \bsqlite_popen\s*\(
    - \bsqlite_array_query\s*\(
    - \barrayQuery\s*\(
    - \bsingleQuery\s*\(
    - \bsqlite_query\s*\(
    - \bsqlite_exec\s*\(
    - \bsqlite_single_query\s*\(
    - \bsqlite_unbuffered_query\s*\(
    - \bsybase_query\s*\(
    - \bsybase_unbuffered_query\s*\(


- ID: PHP_EVAL_001
  name: "Evaluate php code in functions like 'eval'"
  severity: High
  confidence: Medium
  references: []
  patterns:
    - \bassert\s*\(
    - \bcreate_function\s*\(
    - \beval\s*\(
    - \bmb_ereg_replace\s*\(
    - \bmb_eregi_replace\s*\(
    - \bpreg_filter\s*\(
    - \bpreg_replace\s*\(
    - \bpreg_replace_callback\s*\(


- ID: PHP_REFLECTION_INJ_001
  name: "Use PHP reflection mechanism to control program flow"
  severity: Medium
  confidence: Low
  references: ['https://www.owasp.org/index.php/Unsafe_use_of_Reflection']
  patterns:
    - \bevent_buffer_new\s*\(
    - \bevent_set\s*\(
    - \biterator_apply\s*\(
    - \bforward_static_call\s*\(
    - \bforward_static_call_array\s*\(
    - \bcall_user_func\s*\(
    - \bcall_user_func_array\s*\(
    - \barray_diff_uassoc\s*\(
    - \barray_diff_ukey\s*\(
    - \barray_filter\s*\(
    - \barray_intersect_uassoc\s*\(
    - \barray_intersect_ukey\s*\(
    - \barray_map\s*\(
    - \barray_reduce\s*\(
    - \barray_udiff\s*\(
    - \barray_udiff_assoc\s*\(
    - \barray_udiff_uassoc\s*\(
    - \barray_uintersect\s*\(
    - \barray_uintersect_assoc\s*\(
    - \barray_uintersect_uassoc\s*\(
    - \barray_walk\s*\(
    - \barray_walk_recursive\s*\(
    - \bassert_options\s*\(
    - \bregister_shutdown_function\s*\(
    - \bregister_tick_function\s*\(
    - \brunkit_method_add\s*\(
    - \brunkit_method_copy\s*\(
    - \brunkit_method_redefine\s*\(
    - \brunkit_method_rename\s*\(
    - \brunkit_function_add\s*\(
    - \brunkit_function_copy\s*\(
    - \brunkit_function_redefine\s*\(
    - \brunkit_function_rename\s*\(
    - \bsession_set_save_handler\s*\(
    - \bset_error_handler\s*\(
    - \bset_exception_handler\s*\(
    - \bspl_autoload\s*\(
    - \bspl_autoload_register\s*\(
    - \bsqlite_create_aggregate\s*\(
    - \bsqlite_create_function\s*\(
    - \bstream_wrapper_register\s*\(
    - \buasort\s*\(
    - \buksort\s*\(
    - \busort\s*\(
    - \byaml_parse\s*\(
    - \byaml_parse_file\s*\(
    - \byaml_parse_url\s*\(
    - \beio_busy\s*\(
    - \beio_chmod\s*\(
    - \beio_chown\s*\(
    - \beio_close\s*\(
    - \beio_custom\s*\(
    - \beio_dup2\s*\(
    - \beio_fallocate\s*\(
    - \beio_fchmod\s*\(
    - \beio_fchown\s*\(
    - \beio_fdatasync\s*\(
    - \beio_fstat\s*\(
    - \beio_fstatvfs\s*\(
    - \bpreg_replace_callback\s*\(
    - \bdotnet_load\s*\(


- ID: PHP_FILE_INCLUSION_001
  name: "Evaluate php code in functions like 'eval'"
  severity: Medium
  confidence: Low
  references: []
  patterns:
    - \binclude\s+
    - \binclude_once\b
    - \bparsekit_compile_file\s*\(
    - \bphp_check_syntax\s*\(
    - \brequire\s+
    - \brequire_once\b
    - \brunkit_import\s*\(
    - \bset_include_path\s*\(
  evaluate: php_file_inclusion_001_evaluate


- ID: PHP_FILE_OPERATION_001
  name: "File operation"
  severity: Medium
  confidence: Low
  references: []
  references: []
  patterns:
    - \bbzwrite\s*\(
    - \bchmod\s*\(
    - \bchgrp\s*\(
    - \bchown\s*\(
    - \bcopy\s*\s*\(
    - \bdio_write\s*\(
    - \beio_chmod\s*\(
    - \beio_chown\s*\(
    - \beio_mkdir\s*\(
    - \beio_mknod\s*\(
    - \beio_rmdir\s*\(
    - \beio_write\s*\(
    - \beio_unlink\s*\(
    - \berror_log\s*\(
    - \bevent_buffer_write\s*\(
    - \bfile_put_contents\s*\(
    - \bfputcsv\s*\(
    - \bfputs\s*\(
    - \bfprintf\s*\(
    - \bftruncate\s*\(
    - \bfwrite\s*\(
    - \bgzwrite\s*\(
    - \bgzputs\s*\(
    - \bloadXML\s*\(
    - \bmkdir\s*\(
    - \bmove_uploaded_file\s*\(
    - \bposix_mknod\s*\(
    - \brecode_file\s*\(
    - \brename\s*\(
    - \brmdir\s*\(
    - \bshmop_write\s*\(
    - \btouch\s*\(
    - \bunlink\s*\s*\(
    - \bvfprintf\s*\(
    - \bxdiff_file_bdiff\s*\(
    - \bxdiff_file_bpatch\s*\(
    - \bxdiff_file_diff_binary\s*\(
    - \bxdiff_file_diff\s*\(
    - \bxdiff_file_merge3\s*\(
    - \bxdiff_file_patch_binary\s*\(
    - \bxdiff_file_patch\s*\(
    - \bxdiff_file_rabdiff\s*\(
    - \byaml_emit_file\s*\(


- ID: PHP_XPATH_INJ_001
  name: "Execute xpath command"
  severity: High
  confidence: Medium
  references: []
  patterns:
    - \bxpath_eval\s*\(
    - \bxpath_eval_expression\s*\(
    - \bxptr_eval\s*\(


- ID: PHP_LDAP_INJ_001
  name: "Evaluate php code in functions like 'eval'"
  severity: High
  confidence: Medium
  references: []
  patterns:
    - \bldap_add\s*\(
    - \bldap_delete\s*\(
    - \bldap_list\s*\(
    - \bldap_read\s*\(
    - \bldap_search\s*\(



- ID: PHP_PROTOCOL_INJ_001
  name: "Protocol inject"
  severity: Medium
  confidence: Low
  references: []
  patterns:
    - \bcurl_setopt\s*\(
    - \bcurl_setopt_array\s*\(
    - \bcyrus_query\s*\(
    - \berror_log\s*\(
    - \bfsockopen\s*\(
    - \bftp_chmod\s*\(
    - \bftp_exec\s*\(
    - \bftp_delete\s*\(
    - \bftp_fget\s*\(
    - \bftp_get\s*\(
    - \bftp_nlist\s*\(
    - \bftp_nb_fget\s*\(
    - \bftp_nb_get\s*\(
    - \bftp_nb_put\s*\(
    - \bftp_put\s*\(
    - \bget_headers\s*\(
    - \bimap_open\s*\(
    - \bimap_mail\s*\(
    - \bmb_send_mail\s*\(
    - \bldap_connect\s*\(
    - \bmsession_connect\s*\(
    - \bpfsockopen\s*\(
    - \bsession_register\s*\(
    - \bsocket_bind\s*\(
    - \bsocket_connect\s*\(
    - \bsocket_send\s*\(
    - \bsocket_write\s*\(
    - \bstream_socket_client\s*\(
    - \bstream_socket_server\s*\(
    - \bprinter_open\s*\(



- ID: PHP_OBJ_INJ_001
  name: "Serialize operation"
  severity: High
  confidence: Low
  references: []
  patterns:
    - \bunserialize\s*\(
    - \byaml_parse\s*\(


