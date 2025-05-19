import os
import shutil
import macos_dylib_solver
import subprocess
from typing import List

expected_version_str = ""
version_seps: List[str] = []
homebrew_python_path = ""
homebrew_tk_path = ""


# 处理可执行文件和libpython
def process_exe_and_libpy():
    # 处理主要的可执行文件，这个可执行文件藏的很深，不能用bin文件夹下面的那个，要用这个
    homebrew_python_exe_path = (
        f"{homebrew_python_path}/Resources/Python.app/Contents/MacOS/Python"
    )
    shutil.copyfile(homebrew_python_exe_path, "../python")

    # macOS上面的libpython起名居然是Python，很容易跟可执行文件搞混，所以我决定把它重新命名回libpython
    homebrew_libpython_path = f"{homebrew_python_path}/Python"
    shutil.copyfile(homebrew_libpython_path, "../libpython.dylib")

    # 复制过来的可执行文件要进行处理才能用，首先是要把libpython的install name改掉，然后再把可执行文件的依赖改掉
    macos_dylib_solver.process_deps("../libpython.dylib")
    os.remove("../libpython.dylib")
    subprocess.run(
        [
            "install_name_tool",
            "-change",
            homebrew_libpython_path,
            "@executable_path/dylib/libpython.dylib",
            "../python",
        ],
        check=True,
    )

    # dylib签名后面会一起搞，这里先把exe签名，然后赋予可执行权限
    subprocess.run(
        [
            "codesign",
            "-f",
            "-s",
            "-",
            "../python",
        ],
        check=True,
    )
    subprocess.run(
        [
            "chmod",
            "+x",
            "../python",
        ],
        check=True,
    )


# 复制标准库过来
def process_stdlib():
    homebrew_python_stdlib_path = (
        f"{homebrew_python_path}/lib/python{version_seps[0]}.{version_seps[1]}"
    )
    shutil.copytree(
        homebrew_python_stdlib_path,
        f"../lib/python{version_seps[0]}.{version_seps[1]}",
        copy_function=shutil.copyfile,
        dirs_exist_ok=True,
    )

    # 直接整个文件夹复制过来会有一大堆没有用的东西，都应该删掉
    rubbish_dirs = [
        f"config-{version_seps[0]}.{version_seps[1]}-darwin",
        "site-packages",
        "idlelib",
        "test",
        "turtledemo",
        "unittest",
        "venv",
        "ensurepip",
        "tkinter/test",
    ]

    for i in rubbish_dirs:
        shutil.rmtree(
            f"../lib/python{version_seps[0]}.{version_seps[1]}/{i}", ignore_errors=True
        )

    rubbish_files = ["sitecustomize.py"]

    for i in rubbish_files:
        path = f"../lib/python{version_seps[0]}.{version_seps[1]}/{i}"
        if os.path.exists(path):
            os.remove(path)

    # 处理lib-dynload的没用东西
    lib_dynload_path = f"../lib/python{version_seps[0]}.{version_seps[1]}/lib-dynload"
    lib_dynload_files = os.listdir(lib_dynload_path)

    for i in lib_dynload_files:
        filename = os.path.basename(i)
        if filename.startswith("_test") and filename.endswith(".so"):
            os.remove(os.path.join(lib_dynload_path, filename))

    # 删干净之后，就要加入一些必要的东西了
    # 先加入pip和wheel
    pip_path = f"{homebrew_python_path}/lib/python{version_seps[0]}.{version_seps[1]}/site-packages/pip"
    shutil.copytree(
        pip_path,
        f"../lib/python{version_seps[0]}.{version_seps[1]}/pip",
        copy_function=shutil.copyfile,
        dirs_exist_ok=True,
    )

    pip_path = f"{homebrew_python_path}/lib/python{version_seps[0]}.{version_seps[1]}/site-packages/wheel"
    shutil.copytree(
        pip_path,
        f"../lib/python{version_seps[0]}.{version_seps[1]}/wheel",
        copy_function=shutil.copyfile,
        dirs_exist_ok=True,
    )

    # 然后加入tkinter
    shutil.copyfile(
        homebrew_tk_path,
        os.path.join(lib_dynload_path, os.path.basename(homebrew_tk_path)),
    )


if __name__ == "__main__":
    expected_version_str = input("请输入想要移植的Homebrew python版本（如3.13.3）：")
    version_seps = list(map(lambda x: x.strip(), expected_version_str.split(".")))

    # 检查版本号格式
    if len(version_seps) != 3 or any(map(lambda x: not x.isdigit(), version_seps)):
        print("版本号格式错误，请输入正确的版本号")
        exit(2)

    # 检查版本号是否存在
    homebrew_python_path = f"/opt/homebrew/Cellar/python@{version_seps[0]}.{version_seps[1]}/{version_seps[0]}.{version_seps[1]}.{version_seps[2]}/Frameworks/Python.framework/Versions/{version_seps[0]}.{version_seps[1]}"
    if not os.path.exists(homebrew_python_path):
        print(f"Homebrew python@{version_seps[0]}.{version_seps[1]}版本不存在")
        exit(3)

    homebrew_tk_path = f"/opt/homebrew/Cellar/python-tk@{version_seps[0]}.{version_seps[1]}/{version_seps[0]}.{version_seps[1]}.{version_seps[2]}/libexec/_tkinter.cpython-{version_seps[0]}{version_seps[1]}-darwin.so"
    if not os.path.exists(homebrew_tk_path):
        print(f"Homebrew python-tk@{version_seps[0]}.{version_seps[1]}版本不存在")
        exit(4)

    # 创建工作目录
    print(f"正在尝试移植{expected_version_str}版本的python到父目录")
    os.makedirs("../dylib", exist_ok=False)
    os.makedirs("../lib", exist_ok=False)

    # 处理可执行文件和libpython
    process_exe_and_libpy()
    print("可执行文件和libpython处理完成，准备复制标准库")

    # 处理标准库
    process_stdlib()
    print("标准库处理完成")

    macos_dylib_solver.process_python_bundles(f"{version_seps[0]}.{version_seps[1]}")
