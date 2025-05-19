# macOS嵌入式python
python官方没有提供像Windows那种开箱即可用的embedded python。这使得有些情况下，你必须要在应用中携带一个python运行时的时候，会特别麻烦。
虽说有一个Python-Apple-Support项目提供了一个Python.xcframework的东西，但有的情况下，我就只是想要一个python运行时的时候，把整个framework搞进来难免是有点高射炮打蚊子了。

## 使用方法
**注意！这个工程只限于macOS arm64架构。如需x64版本，请尝试使用builder文件夹下的脚手架自行构建。请查看builder目录下的README文件的说明。**


把这个工程克隆下来，其中的`builder`文件夹是不需要的，那个是用来生成这一个嵌入式python的时候用的一些脚手架。
有效的东西一共就是这五个：`Python`可执行文件、`lib/`是自带的标准库、`dylib/`是所需的动态库、`run.sh`用于执行程序、`pip.sh`用来安装第三方库。

当然，常用的tkinter、sqlite、crypto、ssl功能一样不缺，全部都移植好了。

### 执行脚本或者运行python环境
很简单，直接`./run.sh main.py`即可，或者`./run.sh`你就会得到一个交互式环境。

### pip安装
很简单，直接`./pip.sh install numpy`这样就可以了，用法跟原版pip一样。

注意，`pip uninstall`可能会小有点问题，需要进入到`lib/site-packages`文件夹下手动删掉就行。当然，这个对于嵌入式python来说，全部删掉重新install也不是啥大问题。

### 虚拟环境？
虚拟个锤子，这都是嵌入式python了，你把这套运行环境拷贝一份不就好了？

## 实现原理
我们是基于homebrew版本的python进行移植的。Homebrew版本的python已经8成接近于一个嵌入式的了，只不过我们在此基础上把某些install name进行修改，就得到了最终可以开箱即用的嵌入式python运行时。

最坑的点其实就在于怎么找到真正的可执行文件和libpython，剩下的都简单。我们以`python 3.13.3`为例子。

Homebrew安装python的路径理论上应该在`/opt/homebrew/Cellar/python@3.13/3.13.3`，然而，当你想当然看到有一个`bin`文件夹，里面还恰好有一个软链接`python3`的可执行文件的时候，别高兴得太早。

那个`python3`可执行文件的软链接虽然指向的是`/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3`这个文件，但是你复制出来就会发现这个不对劲。这个可执行文件是一个空壳，通过分析发现这个可执行文件其实内部只是调用了一个fork（Unix下新建进程的系统调用），而fork出去的子进程，实际上是这个文件：
`/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Resources/Python.app/Contents/MacOS/Python`
坑爹的属于是，搞大半天才找到了真正的可执行文件。

然后找到了这个真正的可执行文件，它其实才几十KB，很显然真正的东西应该是在动态链接库的。我们直接调用`otool -L /opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Resources/Python.app/Contents/MacOS/Python`命令，就可以看到这个可执行文件，依赖了一个动态库，这个动态库在`/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/Python`这个路径。

这又是个坑爹玩意，明明是一个动态链接库，你个鬼东西起名起的跟可执行文件一毛一样，真的误导性极强。这个应该叫`libpython.dylib`才对，毕竟Windows上这玩意叫`python.dll`。还好，`libpython.dylib`无其它第三方库依赖，处理起来不麻烦。

找到了真正的可执行文件和libpython之后，剩下的事情就简单了，直接移步`builder/`文件夹下的`main.py`和`macOS_dylib_solver.py`，无非就是改一下名字而已。