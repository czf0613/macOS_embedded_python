from typing import List, Set, Dict, Tuple, Optional
import subprocess
import os
import shutil
import glob

# 这个脚本的作用是解析macOS上的动态库，获取它们的依赖关系，然后统一输出到一个目录下面，然后生成的可执行文件直接把这个路径加入rpath或修改对应的install name就可以了
final_output_dir = "../dylib/"


# 复制文件，src可能是软链接，需要进行处理
# 这个复制只复制文件内容，不会拷贝权限等等，比较适合动态库这个场景
# 默认不会复制已经存在的文件
def copy_file(src: str, dest: str):
    if os.path.exists(dest):
        return

    # 目标目录必须确保存在
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    real_path = os.path.realpath(src)
    shutil.copyfile(real_path, dest)


# 获取一个库指定的rpath，后面需要用到来解析绝对路径
def get_lib_rpaths(lib_path: str) -> Set[str]:
    otool_output = subprocess.check_output(["otool", "-l", lib_path], text=True)
    lines = otool_output.splitlines()

    rpaths = set()  # rpath可能有多个，所以用list来存储
    for i, line in enumerate(lines):
        if "LC_RPATH" in line:
            # RPATH 的路径通常在接下来的两行
            path_line = lines[i + 2]
            if "path" in path_line:
                rpath = path_line.strip().split(" ")[1]
                rpaths.add(rpath)

    return rpaths


# 解析单个第三方库的依赖，只能解析一层，解析出来的路径很可能是一个软链接，真正复制文件的时候需要进行处理
# 返回的是元组，第0个元素是用到的绝对路径的第三方库，第1个元素是用到的是rpath的动态库的路径，后面需要修正这些
def get_dependencies(
    library_path: str, is_exe: bool
) -> Tuple[List[str], Dict[str, str]]:
    cmd_output = subprocess.check_output(["otool", "-L", library_path], text=True)
    lines = cmd_output.splitlines()[1 if is_exe else 2 :]

    def parse_line(line: str) -> str:
        content = line.strip()
        parts = content.split()
        return parts[0].strip()

    beatified_lines = map(parse_line, lines)
    result = ([], {})

    for dep in beatified_lines:
        # 把动态库里面带@的踢出来
        if dep.startswith("@rpath"):
            print(f"{library_path} has rpath dynamic lib: {dep}")

            # 找到这个库本身设置的rpath，和它自身的父目录
            rpaths = get_lib_rpaths(library_path)
            rpaths.add(os.path.dirname(library_path))

            dep_actual_path: Optional[str] = None
            for rpath in rpaths:
                possible_path = dep.replace("@rpath", rpath)
                possible_abspath = os.path.abspath(
                    possible_path
                )  # rpath里面可能有../之类的这种父目录符号，把它处理掉

                if os.path.exists(possible_abspath):
                    result[1][dep] = possible_abspath
                    dep_actual_path = possible_abspath
                    print(
                        f"rpath dependency {dep} in {library_path} is solved to {possible_abspath}"
                    )
                    break

            if dep_actual_path is None:
                # 这个库的rpath没有找到，那肯定是寄了
                print(f"rpath in {library_path} could not be extracted")
                exit(1)
        elif dep.startswith("@executable_path") or dep.startswith("@loader_path"):
            # 这些库暂时没办法处理，一般它们不会出现在第三方库里面出现的话，报错吧
            print(f"{library_path} has unsolvable special dynamic path: {dep}")
            exit(1)
        else:
            # 这个库是一个绝对路径的动态库，直接用它的路径就行了
            if not dep.startswith("/System/") and not dep.startswith("/usr/"):
                result[0].append(dep)

    return result


# 把原本的依赖路径改成@executable_path/dylib/下面的路径
def change_dep_name(lib_path: str, old_dep: str):
    name = os.path.basename(old_dep)

    subprocess.run(
        [
            "install_name_tool",
            "-change",
            old_dep,
            f"@executable_path/dylib/{name}",
            lib_path,
        ],
        check=True,
    )


# 把这个库的install name改成@executable_path/dylib/下面的路径
def change_install_name(lib_path: str):
    name = os.path.basename(lib_path)

    subprocess.run(
        [
            "install_name_tool",
            "-id",
            f"@executable_path/dylib/{name}",
            lib_path,
        ],
        check=True,
    )


# 抹掉这个库自带的rpath信息，后面可能要重新写
def remove_rpaths(lib_path: str):
    rpaths = get_lib_rpaths(lib_path)

    for rpath in rpaths:
        subprocess.run(
            ["install_name_tool", "-delete_rpath", rpath, lib_path], check=True
        )


# 递归处理一个库或可执行文件下的所有依赖
def process_deps(initial_lib: str, is_exe: bool = False):
    lib_path = initial_lib

    # 如果输入的是一个可执行文件，那就不应该复制，并且lib_path应该就是它自身
    if not is_exe:
        # 先复制
        lib_path = os.path.join(final_output_dir, os.path.basename(initial_lib))
        if os.path.exists(lib_path):
            # 这个库已经处理过了，直接返回
            return

        copy_file(initial_lib, lib_path)
        # 复制完当场改变install name，然后抹掉它自带的rpath信息
        change_install_name(lib_path)

    remove_rpaths(lib_path)

    (dylibs, rpath_dylibs) = get_dependencies(initial_lib, is_exe)
    if len(dylibs) == 0 and len(rpath_dylibs) == 0:
        # 处理完了就递归结束呗
        return

    print(f"{initial_lib} 1st order deps:", dylibs, rpath_dylibs, sep=os.linesep)
    if len(dylibs) > 0:
        for lib in dylibs:
            # 把依赖改掉，然后递归处理
            change_dep_name(lib_path, lib)

            process_deps(lib)

    if len(rpath_dylibs) > 0:
        for k, v in rpath_dylibs.items():
            change_dep_name(lib_path, k)

            # 这个库的rpath已经被处理过了，所以直接用它的路径就行了
            process_deps(v)


if __name__ == "__main__":
    # cpython里面有很多用原生实现的库，那些库可能会依赖一些dylibs，也要处理
    bundles = glob.glob(f"../lib/python3.13/lib-dynload/*.so")

    for bundle in bundles:
        # 处理python的动态库，这个库相当于macOS上面的bundle类型，可以复用exe的处理逻辑
        process_deps(bundle, True)

    subprocess.run(
        f"codesign -f -s - {final_output_dir}*.dylib",
        check=True,
        shell=True,
    )

    subprocess.run(
        f"codesign -f -s - ../lib/python3.13/lib-dynload/*.so",
        check=True,
        shell=True,
    )
