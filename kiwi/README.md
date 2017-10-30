

## About

`kiwi`是一款基于文本的代码安全审计工具

## 使用

`kiwi`中涉及的3个环境变量

- KIWI_DATA_PATH  指定kiwi特征定义目录位置，如果不指定则需要在命令行使用参数**-f/--feature_dir**指定
- KIWI_OPENGROK_BASE 指定opengrok的起始地址，如果扫描的代码是通过opengrok组织的，则建议使用此项，这样扫描报告会自动连接的opengrok
- KIWI_REPORT_PATH 指定report输出的目录，用于`kiwi-report`，如果不指定则需要使用**-d/--report_path**参数指定