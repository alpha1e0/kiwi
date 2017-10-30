
# 1 关于

`kiwi` 项目是一个源代码安全审计工具集。包含：

* kiwi审计工具. 基于文本的安全源码审计工具，根据文件类型使用相应的 **漏洞特征** 定义文件，查找源码中可能会存在安全风险的代码。
* kiwilime源码阅读插件. Sublime Text 3 插件，和 kiwi 配合使用，支持调动 kiwi 进行源码审计、高亮语法展示漏洞、快捷跳转到漏洞位置、快速搜索等。
* kiwi_data. 默认的 **漏洞特征** 规则文件。

本工具集适用于以下人员、场景：

- 黑客、安全研究人员、安全测试人员
- 多种语言的代码审计工作
- 大规模软件的代码审计工作

代码安全审计工作一般需要2个辅助工具：

1. 代码审计工具，能够从代码中找到可能存在安全问题的位置，并且生成可视化的报告。例如开源的rips、bandit，商业的fortify、checkmarx
2. 一个方便阅读代码的工具，能够索引代码实现跳转。例如SourceInsight、vim+ctags+cscope、opengrok，商业的fortify、checkmarx往往也支持

对于商业工具来讲，面对人群往往是“非专业人士”，追求简单、易用、误报率底、报告形式多样。商业工具往往是基于语法分析的引擎、并且能够简单分析数据流。

但这些特性对于“专业人士”来讲往往无足轻重。实际上，对于经常做代码审计的人来说，“灵活性”才是最重要的，例如一个常见的情景：在审计中发现一个可疑的点，然后需要迅速找到代码中所有相关位置；而商业工具规则定制往往比较复杂，不能很好得满足需求。商业工具提供的误报率低、数据流分析，对于经常做代码审计的人来说也并非必须的内容。

反观开源工具，往往存在支持的语言少、大规模代码审计的时候效率低下等问题，因此在做代码审计的时候往往需要组合使用多工具。

`kiwi` 工具是在这种需求下产生的：

- 基于文本（正则+插件确认）的检测工具，不追求误报率、数据流分析等“花哨”的功能
- 能够非常方便的定制自己的规则
- 能够关联报告，报告可以和本项目的 `kiwilime` 工具结合使用，可以和 `opengrok`（大规模代码阅读工具）结合
- 能够非常方便得编辑检测报告，例如去掉已经确认没有风险的问题

因此，在遇到中小规模的代码审计项目时候，可以使用 `kiwi+kiwilime`工具，而对于大规模的代码审计项目，可以使用 `kiwi+opengrok`的方法

注： `opengrok`工具是一个大型源码阅读工具，请参考 [这里](https://github.com/OpenGrok)


# 2 安装

## 2.1 kiwi 安装

使用一下命令安装kiwi：

    git clone https://github.com/alpha1e0/kiwi.git
    cd kiwi/kiwi
    python setup.py install


## 2.2 kiwilime 安装

**Step 1.** 

获取 kiwilime

    git clone https://github.com/alpha1e0/kiwi.git

**Step 2.** 

打开 Sublime Text 3 package-directory

    Preferences --> Browse packages

**Step 3.**

将 **kiwilime** 目录整个 copy 到 package-directory


# 3 Usage

### 3.1 kiwi 使用

见 **kiwi** 目录下的 **README.md**

### 3.2 kiwilime 使用

见 **kiwilime** 目录下的 **README.md**