import logging
import subprocess
import re
import shutil


class VolumeController:
    """Linux 音量控制器"""

    def __init__(self):
        self.logger = logging.getLogger("VolumeController")
        # 检测可用的音量控制工具
        self.linux_tool = None

        def cmd_exists(cmd):
            return shutil.which(cmd) is not None

        # 按优先级检查工具
        if cmd_exists("pactl"):
            self.linux_tool = "pactl"
        elif cmd_exists("wpctl"):
            self.linux_tool = "wpctl"
        elif cmd_exists("amixer"):
            self.linux_tool = "amixer"
        elif cmd_exists("alsamixer") and cmd_exists("expect"):
            self.linux_tool = "alsamixer"

        if not self.linux_tool:
            self.logger.error("未找到可用的 Linux 音量控制工具")
            raise Exception("未找到可用的 Linux 音量控制工具")

        self.logger.debug(f"Linux 音量控制初始化成功，使用: {self.linux_tool}")

    def get_volume(self):
        """获取当前音量 (0-100)"""
        return self._get_linux_volume()

    def set_volume(self, volume):
        """设置音量 (0-100)"""
        # 确保音量在有效范围内
        volume = max(0, min(100, volume))
        self._set_linux_volume(volume)

    def _get_linux_volume(self):
        """获取 Linux 音量"""
        if self.linux_tool == "pactl":
            return self._get_pactl_volume()
        elif self.linux_tool == "wpctl":
            return self._get_wpctl_volume()
        elif self.linux_tool == "amixer":
            return self._get_amixer_volume()
        return 70

    def _set_linux_volume(self, volume):
        """设置 Linux 音量"""
        if self.linux_tool == "pactl":
            self._set_pactl_volume(volume)
        elif self.linux_tool == "wpctl":
            self._set_wpctl_volume(volume)
        elif self.linux_tool == "amixer":
            self._set_amixer_volume(volume)
        elif self.linux_tool == "alsamixer":
            self._set_alsamixer_volume(volume)

    def _get_pactl_volume(self):
        """使用 pactl 获取音量"""
        try:
            result = subprocess.run(
                ["pactl", "list", "sinks"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Volume:' in line and 'front-left:' in line:
                        match = re.search(r'(\d+)%', line)
                        if match:
                            return int(match.group(1))
        except Exception as e:
            self.logger.debug(f"通过 pactl 获取音量失败: {e}")
        return 70

    def _set_pactl_volume(self, volume):
        """使用 pactl 设置音量"""
        try:
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"],
                capture_output=True,
                text=True
            )
        except Exception as e:
            self.logger.warning(f"通过 pactl 设置音量失败: {e}")

    def _get_wpctl_volume(self):
        """使用 wpctl 获取音量"""
        try:
            result = subprocess.run(
                ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                capture_output=True,
                text=True,
                check=True
            )
            return int(float(result.stdout.split(' ')[1]) * 100)
        except Exception as e:
            self.logger.debug(f"通过 wpctl 获取音量失败: {e}")
        return 70

    def _set_wpctl_volume(self, volume):
        """使用 wpctl 设置音量"""
        try:
            subprocess.run(
                ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{volume}%"],
                capture_output=True,
                text=True,
                check=True
            )
        except Exception as e:
            self.logger.warning(f"通过 wpctl 设置音量失败: {e}")

    def _get_amixer_volume(self):
        """使用 amixer 获取音量"""
        try:
            result = subprocess.run(
                ["amixer", "get", "Master"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                match = re.search(r'(\d+)%', result.stdout)
                if match:
                    return int(match.group(1))
        except Exception as e:
            self.logger.debug(f"通过 amixer 获取音量失败: {e}")
        return 70

    def _set_amixer_volume(self, volume):
        """使用 amixer 设置音量"""
        try:
            subprocess.run(
                ["amixer", "sset", "Master", f"{volume}%"],
                capture_output=True,
                text=True
            )
        except Exception as e:
            self.logger.warning(f"通过 amixer 设置音量失败: {e}")

    def _set_alsamixer_volume(self, volume):
        """使用 alsamixer 设置音量"""
        try:
            script = f"""
            spawn alsamixer
            send "m"
            send "{volume}"
            send "%"
            send "q"
            expect eof
            """
            subprocess.run(
                ["expect", "-c", script],
                capture_output=True,
                text=True
            )
        except Exception as e:
            self.logger.warning(f"通过 alsamixer 设置音量失败: {e}")

    @staticmethod
    def check_dependencies():
        """检查并报告缺少的依赖"""
        import shutil
        tools = ["pactl", "wpctl", "amixer", "alsamixer"]
        found = False
        missing = []
        for tool in tools:
            if shutil.which(tool):
                found = True
                break
            else:
                missing.append(tool)

        if not found:
            print(f"警告: 音量控制需要以下依赖，但未找到: {', '.join(missing)}")
            print("请使用以下命令安装缺少的依赖:")
            print("sudo apt-get install " + " ".join(missing))
            return False

        return True