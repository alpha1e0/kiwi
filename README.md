
# 1 关于

`kiwi` 项目是一个源代码安全审计工具。适用于黑客、安全研究人员、安全测试人员，支持多种语言的代码审计工作。

代码安全审计工作一般需要2个辅助工具：

1. 代码审计(搜索）工具，能够从代码中找到可能存在安全问题的位置，并且生成可视化的报告。
2. 一个方便阅读代码的工具，能够索引代码实现跳转。例如opengrok、SourceInsight、vim+ctags+cscope

`kiwi`是一个基于文本的安全源码审计工具，它不会对源代码进行语法解析，而是使用简单的正则表达式方式搜索代码，同时提供了问题确认机制用于减少误报。

`kiwi`工具可以和`opengrok`工具很好得结合起来，使得扫描报告中的问题可以直接链接到相应的代码。如果经常进行源代码审计工作，强烈建议使用 `kiwi + opengrok` 的解决方案，

`kiwi`是一个规则和框架完全分离的系统，这样用户可以方便得自定义规则，而不用涉及任何框架层面的修改。

在该项目中有3个目录，分别对应3个子项目：

- kiwi。该目录为`kiwi`工具的主体框架，需要安装到系统中。
- kiwi_data。该目录为`kiwi`的缺省规则目录，放到系统中任意位置即可，用户可在此目录修改、编写自己的搜索规则
- kiwilime。该目录提供了一个`sublime text3`插件，用于和`kiwi`配合使用，可以高亮显示扫描结果，快捷键跳转到代码`sublime text3`打开的代码目录相应代码行数等。

注： `opengrok`工具是一个B/S架构的大型源码阅读工具，请参考 [这里](https://github.com/oracle/opengrok)

## 1.1 kiwi的优劣

目前主流的源码审计工具多采用 **语法解析+插件检测** 的方式实现，即工具会对目标代码做语法分析，生成语法树，然后遍历语法树的每个节点，对每个节点调用所有插件（插件实现检测语法节点是否存在安全漏洞）。

**语法解析+插件检测** 的这种方式更加精确，例如检测eval函数，正则表达式的方式可能会匹配注释，而语法解析的方式则不会，并且语法解析的方式可以回溯语法节点从而做到“数据流分析”。

但是 **语法解析+插件检测** 的实现方式太过复杂，需要为支持的每一种编程语言编写语法解析模块，代价很大，因此商业性的工具非常昂贵；而开源的工具支持的编程语言种类非常少，很难做到跨多种语言审计。

**语法解析+插件检测** 方式相对于高昂代价来说，带来的收益是有限的。实际上多数商业源码审计工具面向的都是非安全人员，而很多黑客仍在使用 **grep** 来做代码审计。

作者认为目前的这些工具不是很适合专业安全人员、黑客，对于源码审计来说，最具有技术含量，最具有创造性的是**检测规则**，专业安全人员在做源码审计的时候**检测规则**并非一成不变，在一次源码审计的过程中会不断发现一些新的 **危险代码** ，需要不断调整**检测规则**来适应新的变化，因此**自定义检测规则**是对于专业安全人员、黑客来说才是最重要的。

`kiwi`就是这样一个工具，使用它可以很方便得随时更新**检测规则**随时再次进行扫描，`kiwi`虽然在实现原理上落后主流技术，但更加适合专业安全人员。


## 1.2 解决方案选择

这里推荐两种解决方案来实现安全源码审计：

1. kiwi + opengrok。该方案适合大规模的源码审计，可解决**千万行**级别、**团队合作**的源码审计需求（作者所在公司即采用该方案实现）。
2. kiwi + sublime text3 + kiwilime。该方案适合个人桌面级使用，解决**万行及以下**、**单人**代码审计需求。


# 2 安装

## 2.1 kiwi 安装

使用一下命令安装kiwi：

    git clone https://github.com/alpha1e0/kiwi.git
    cd kiwi/kiwi
    python setup.py install


## 2.2 kiwi_data 安装

`kiwi_data` 无需要安装，放到磁盘中某个目录即可，在扫描的时候通过以下两种方式定位到`kiwi_data`目录:

1. 通过 **KIWI_DATA_PATH** 环境变量指定`kiwi_data`目录。（推荐的方式）
2. 在`kiwi`扫描命令行中通过 *-f/--feature_dir* 参数指定`kiwi_data`目录


## 2.3 kiwilime 安装

**Step 1.** 

获取 kiwilime

    git clone https://github.com/alpha1e0/kiwi.git

**Step 2.** 

打开 Sublime Text 3 package-directory

    Preferences --> Browse packages

**Step 3.**

将 **kiwilime** 目录整个 copy 到 package-directory

**kiwilime** 的运行依赖于 [the_platinum_searcher](https://github.com/monochromegane/the_platinum_searcher) 工具，从 [https://github.com/monochromegane/the_platinum_searcher/releases](https://github.com/monochromegane/the_platinum_searcher/releases) 下载编译好的工具，并将其加入到环境变量。

# 3 kiwi 使用

`kiwi`在安装后会生成两个 console-script：
- kiwi. kiwi的扫描入口命令
- kiwi-report. 用于查看db类型的扫描报告

可使用 *kiwi -h* 查看`kiwi`的帮助信息

    [Kiwi 代码安全扫描]
    --------------------------------------------------------------------------------
    usage: kiwi [-h] -t TARGET [-f FEATURE_DIR] [-i FEATURE_IDS [FEATURE_IDS ...]]
                [-e EXTENSIONS [EXTENSIONS ...]] [--igexts IGEXTS [IGEXTS ...]]
                [--excludes EXCLUDES [EXCLUDES ...]] [-c SCTX] [--ectx ECTX]
                [-o OUTPUTS [OUTPUTS ...]] [-v] 

    Kiwi. 代码安全审计工具  

    optional arguments:
      -h, --help            show this help message and exit
      -t TARGET, --target TARGET
                            指定待扫描的目录
      -f FEATURE_DIR, --feature_dir FEATURE_DIR
                            指定漏洞特征定义目录
      -i FEATURE_IDS [FEATURE_IDS ...], --feature_ids FEATURE_IDS [FEATURE_IDS ...]
                            指定加载哪些漏洞特征
      -e EXTENSIONS [EXTENSIONS ...], --extensions EXTENSIONS [EXTENSIONS ...]
                            指定扫描哪些类型文件，例如-e php js则扫描.php .js文件
      --igexts IGEXTS [IGEXTS ...]
                            指定忽略扫描哪些类型文件，例如--igexts php js则忽略扫描.php .js文件
      --excludes EXCLUDES [EXCLUDES ...]
                            忽略扫描文件路径包含关键字的文件
      -c SCTX, --sctx SCTX  指定扫描结果显示的上下文行数
      --ectx ECTX           指定用于评估漏洞所需的上下文信息的文件行数
      -o OUTPUTS [OUTPUTS ...], --outputs OUTPUTS [OUTPUTS ...]
                            指定输出报告文件，支持.txt/.html/.json/.db
      -v, --verbose         详细模式，输出扫描过程信息

使用 *kiwi-report -h* 查看`kiwi-report`的帮助信息

    [Kiwi report browser.]
    --------------------------------------------------------------------------------
    usage: kiwi-report [-h] [-p PORT] [--ip IP] [-d REPORT_PATH]    

    Kiwi. Audit source code for security issuses    

    optional arguments:
      -h, --help            show this help message and exit
      -p PORT, --port PORT  指定监听端口，默认为5000
      --ip IP               指定监听IP
      -d REPORT_PATH, --report_path REPORT_PATH
                            指定扫描报告目录


## 3.1 kiwi扫描示例

在一次扫描中，需要指定：
1. 被扫描对象，即代码目录
2. 使用的扫描规则目录。如果不希望每次都指定规则目录，则可以通过设置环境变量 **KIWI_DATA_PATH** 来永久指定。

扫描示例

    kiwi -t /tmp/vulcodes2 -f /home/xxx/kiwi_data -o result.html
    kiwi -t /tmp/vulcodes2 -o result.db

![扫描截图](https://github.com/alpha1e0/kiwi/raw/master/screenshots/run.png)

## 3.2 规则编写

可通过查看 **kiwi_data** 目录中的内容来获取规则编写示例。

`kiwi`的规则定义均使用`yaml`语法编写，在规则编写中涉及以下几个简单概念：

1、**规则文件**

规则文件是指以 *.feature* 未后缀的文件，记录具体的代码搜索规则定义

2、**评估函数**
评估函数为一个原型固定的python函数，用于后期搜索结果确认。例如搜索到subprocess.check_call(cmd, shell=True)，此时可在评估函数中确认参数shell是否为True，从而减小误报

3、**map文件**

`kiwi`工具是跨语言的，因此需要区分不同编程语言的文件；而map文件就是用来解决编程语言区分的，例如.py文件被认为是python脚本。

4、**senfiles规则文件**

这是一个特殊的规则文件，它的规则仅用于匹配文件名。该规则文件用于帮助安全人员找到敏感文件，例如 xxx_upload.php


**kiwi_data** 的目录结构如下：

    kiwi_data
    .. features                    # 目录，存放规则文件
    .. .. evals                    # 目录，存放评估函数
    .. .. .. py_evaluate_funcs.py  # 文件，评估函数脚本
    .. .. python.feature           # 文件，规则文件
    .. .. java.feature             
    .. filemap                     # 文件，map文件
    .. senfiles                    # 文件，senfiles文件


### 3.2.1 编写map文件

每当新增加一门编程语言的规则时，需要编辑map文件，例如：

    extensions:
      - pattern: "\\.py$"
        scope: python   

      - pattern: "\\.php\\d+$"
        scope: php  

      - pattern: "\\.java$"
        scope: java 

      - pattern: "\\.sh$"
        scope: linux-shell  

    metainfos:
      - pattern: "#!/usr/bin\\w+python"
        scope: python   

      - pattern: "<?php"
        scope: php  

      - pattern: "#!/bin/\\w+sh"
        scope: linux-shell

`kiwi`通过两种方式识别文件类型，**后缀名方式** 和 **metainfo方式**。

其中 **metainfo** 是针对解释型语言的，此类语言往往会在文件的第一行声明使用什么解释器来解析执行，例如python代码文件第一行可能为

    #!/usr/bin/env python

使用任一方式定义map规则即可

### 3.2.2 编写senfiles规则

senfiles规则非常简单，仅仅是一系列的正则表达式，例如：

    patterns:
      - upload
      - download


### 3.2.3 编写规则文件

本节通过示例来说明规则文件的编写，以下规则为某个规则定义文件的部分内容：

    version: 1.0    # 指定规则集的版本

    scopes:         # 指定该规则集适用于哪种场景（编程语言）
      - python  
    

    features:       # features是一个列表是规则定义的主题
    - ID: PY_CMD_INJ_001        # 定义一个容易区分的ID，必选
      name: "Use 'os/commands' module to execute command in shells"  # 添加一句描述性的文本，必选
      references: []            # 漏洞说明相关链接，可选
      severity: High            # 漏洞验证等级，可选
      confidence: High          # 漏洞确信度，可选
      patterns:                 # 正则特征列表
        - os.system
        - popen2.Popen4
        - commands.getoutput
        - commands.getstatusoutput  
    

    - ID: PY_CMD_INJ_002
      name: "Use 'subprocess' module with shell=True to execute command in shells"
      severity: High
      confidence: Medium
      references: []
      patterns:
        - subprocess.call
        - subprocess.Popen
        - subprocess.check_call
        - subprocess.check_output
        - utils.execute
        - utils.execute_with_timeout
      evaluate: py_cmd_inject_0002  # 指定使用的评估函数

简单的规则定义是非常容易的，只需要`ID` `name` `patterns` 三个属性即可。

对于复杂的规则，需要定义评估函数

评估函数示例：

    from kiwi.core.featuremgr import evaluate   

    @evaluate
    def py_cmd_inject_0002(feature, matchctx):
        if matchctx.contains("shell=True"):
            return (feature['severity'], feature['confidence'])
        else:
            return None

评估函数的原型是固定的，使用 `@evaluate` 修饰器来限定，参数有两个：

- feature. feature即使用的规则定义，和规则文件内的内容完全对应
- matchctx. matchctx是一个 `MatchContext` 上下文对象，包含匹配上下文的一些信息

`MatchContext` 提供以下方法、属性供使用：

- 属性: filename. 匹配的代码文件文件名
- 属性: lineno. 匹配的代码文件匹配行行数
- 属性: match_line. 匹配行的代码字符串
- 属性: str_ctx. 匹配的上下文代码字符串（上下文行数和命令行参数--ectx对应）
- 方法: contains(keyword). 返回匹配行是否包含keyword关键字
- 方法: ctx_contains(keyword). 返回匹配上下文是否包含keyword关键字



## 3.3 生成报告

目前`kiwi`支持4中类型报告：

- html. html类型的报告。
- db. db类型的报告，db类型的报告无法直接查阅，需要使用`kiwi-report`来查看
- txt. text类型的报告。
- json. json类型的报告。

其中，db和html类型的报告是最推荐的，txt类型的报告可以使用`kiwilime`这个sublime text查看查看，可以高亮显示。

html报告如下图所示

![html_report](https://github.com/alpha1e0/kiwi/raw/master/screenshots/html_report.png)

使用`kiwi-report`来查看db类型报告时，可以对漏洞进行误报标记。如下图所示

![db_report](https://github.com/alpha1e0/kiwi/raw/master/screenshots/db_report.png)


## 3.4 与opengrok联动

`kiwi`报告可以和`opengrok`联动功能非常实用，即当点击`kiwi`扫描报告（仅限html和db类型报告）中的 “目标文件” 链接时，可以直接跳转到相应代码位置（`opengrok`对应代码的url）。

这里需要配置一个环境变量 **KIWI_OPENGROK_BASE** 该环境变量配置的是`opengrok`工具的代码目录，`kiwi`会使用这个目录作为基准目录来定位代码的位置



