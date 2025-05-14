# macOS嵌入式python
python官方没有提供像Windows那种开箱即可用的embedded python。这使得有些情况下，你必须要在应用中携带一个python运行时的时候，会特别麻烦。
虽说有一个Python-Apple-Support项目提供了一个Python.xcframework的东西，但有的情况下，我就只是想要一个python运行时的时候，把整个framework搞进来难免是有点高射炮打蚊子了。

## 使用方法
**注意！这个工程只限于macOS arm64架构**


把这个工程克隆下来，其中的builder文件夹是不需要的，那个是用来生成这一个嵌入式python的时候用的一些脚手架。有效的东西一共就是这五个：`Python`可执行文件、`lib/`是自带的标准库、`dylib/`是所需的动态库、`run.sh`用于执行程序、`pip.sh`用来安装第三方库。

当然，常用的tkinter、sqlite、crypto、ssl功能一样不缺，全部都移植好了。

### 执行脚本或者运行python环境
很简单，直接`./run.sh main.py`即可，或者`./run.sh`你就会得到一个交互式环境。

### pip安装
很简单，直接`./pip.sh install numpy`这样就可以了，用法跟原版pip一样

### 虚拟环境？
虚拟个锤子，这都是嵌入式python了，你把这套运行环境拷贝一份不就好了？

## 实现原理
我们是基于homebrew版本的python进行移植的。Homebrew版本的python已经8成接近于一个嵌入式的了，只不过我们在此基础上把某些install name进行修改，就得到了最终可以开箱即用的嵌入式python运行时。