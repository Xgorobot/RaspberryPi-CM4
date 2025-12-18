# 在导入 opuslib 之前处理 opus 动态库
import ctypes
import os
import sys
import platform
from pathlib import Path


def setup_opus():
    """设置 opus 动态库"""
    if hasattr(sys, '_opus_loaded'):
        print("opus 库已由其他组件加载")
        return True

    return setup_opus_unix()


def setup_opus_unix():
    """树莓派（Linux系统）下设置opus动态库"""
    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后路径
            base_path = Path(sys.executable).parent
            lib_paths = [
                base_path / 'libs' / 'linux' / 'libopus.so',
                base_path / 'libs' / 'linux' / 'libopus.so.0',
                base_path / 'libopus.so',
                Path('/usr/lib/libopus.so'),
                Path('/usr/lib/libopus.so.0')
            ]
        else:
            # 开发环境路径
            base_path = Path(__file__).parent.parent.parent
            lib_paths = [
                base_path / 'libs' / 'linux' / 'libopus.so',
                base_path / 'libs' / 'linux' / 'libopus.so.0',
                Path('/usr/lib/libopus.so'),
                Path('/usr/lib/libopus.so.0')
            ]

        # 尝试加载所有可能的路径
        for lib_path in lib_paths:
            if lib_path.exists():
                # 加载库并存储引用以防止垃圾回收
                _ = ctypes.cdll.LoadLibrary(str(lib_path))
                print(f"成功加载 opus 库: {lib_path}")
                sys._opus_loaded = True
                return True

        print("未找到 opus 库文件，尝试从系统路径加载")

        # 尝试系统默认路径
        for lib_name in ['libopus.so.0', 'libopus.so']:
            try:
                ctypes.cdll.LoadLibrary(lib_name)
                print(f"已从系统路径加载 {lib_name}")
                sys._opus_loaded = True
                return True
            except Exception:
                continue

        print("从系统路径加载 opus 库失败")
        return False

    except Exception as e:
        print(f"加载 opus 库失败: {e}")
        return False


def _patch_find_library(lib_name, lib_path):
    """修补 ctypes.util.find_library 函数"""
    import ctypes.util
    original_find_library = ctypes.util.find_library

    def patched_find_library(name):
        if name == lib_name:
            return lib_path
        return original_find_library(name)

    ctypes.util.find_library = patched_find_library