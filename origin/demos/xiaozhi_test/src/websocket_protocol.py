import json

from src.constants.constants import AbortReason, ListeningMode


class Protocol:
    def __init__(self):
        self.session_id = ""
        # 初始化回调函数为None
        self.on_incoming_json = None
        self.on_incoming_audio = None
        self.on_audio_channel_opened = None
        self.on_audio_channel_closed = None
        self.on_network_error = None

    def on_incoming_json(self, callback):
        """设置JSON消息接收回调函数"""
        self.on_incoming_json = callback

    def on_incoming_audio(self, callback):
        """设置音频数据接收回调函数"""
        self.on_incoming_audio = callback

    def on_audio_channel_opened(self, callback):
        """设置音频通道打开回调函数"""
        self.on_audio_channel_opened = callback

    def on_audio_channel_closed(self, callback):
        """设置音频通道关闭回调函数"""
        self.on_audio_channel_closed = callback

    def on_network_error(self, callback):
        """设置网络错误回调函数"""
        self.on_network_error = callback

    async def send_text(self, message):
        """发送文本消息的抽象方法，需要在子类中实现"""
        raise NotImplementedError("send_text方法必须由子类实现")

    async def send_abort_speaking(self, reason):
        """发送中止语音的消息"""
        message = {
            "session_id": self.session_id,
            "type": "abort"
        }
        if reason == AbortReason.WAKE_WORD_DETECTED:
            message["reason"] = "wake_word_detected"
        await self.send_text(json.dumps(message))

    async def send_wake_word_detected(self, wake_word):
        """发送检测到唤醒词的消息"""
        message = {
            "session_id": self.session_id,
            "type": "listen",
            "state": "detect",
            "text": wake_word
        }
        await self.send_text(json.dumps(message))

    async def send_start_listening(self, mode):
        """发送开始监听的消息"""
        mode_map = {
            ListeningMode.ALWAYS_ON: "realtime",
            ListeningMode.AUTO_STOP: "auto",
            ListeningMode.MANUAL: "manual"
        }
        message = {
            "session_id": self.session_id,
            "type": "listen",
            "state": "start",
            "mode": mode_map[mode]
        }
        await self.send_text(json.dumps(message))

    async def send_stop_listening(self):
        """发送停止监听的消息"""
        message = {
            "session_id": self.session_id,
            "type": "listen",
            "state": "stop"
        }
        await self.send_text(json.dumps(message))

    async def send_iot_descriptors(self, descriptors):
        """发送物联网设备描述信息"""
        message = {
            "session_id": self.session_id,
            "type": "iot",
            "descriptors": json.loads(descriptors) if isinstance(descriptors, str) else descriptors
        }
        await self.send_text(json.dumps(message))

    async def send_iot_states(self, states):
        """发送物联网设备状态信息"""
        message = {
            "session_id": self.session_id,
            "type": "iot",
            "states": json.loads(states) if isinstance(states, str) else states
        }
        await self.send_text(json.dumps(message))




import asyncio
import json
import logging
import websockets

from src.constants.constants import AudioConfig
from src.utils.config_manager import ConfigManager
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class WebsocketProtocol(Protocol):
    def __init__(self):
        super().__init__()
        # 获取配置管理器实例
        self.config = ConfigManager.get_instance()
        self.websocket = None
        self.connected = False
        self.hello_received = None  # 初始化时先设为 None
        self.WEBSOCKET_URL = self.config.get_config("SYSTEM_OPTIONS.NETWORK.WEBSOCKET_URL")
        self.HEADERS = {
            "Authorization": f"Bearer {self.config.get_config('SYSTEM_OPTIONS.NETWORK.WEBSOCKET_ACCESS_TOKEN')}",
            "Protocol-Version": "1",
            "Device-Id": self.config.get_config("SYSTEM_OPTIONS.DEVICE_ID"),  # 获取设备MAC地址
            "Client-Id": self.config.get_config("SYSTEM_OPTIONS.CLIENT_ID")
        }

    async def connect(self) -> bool:
        """连接到WebSocket服务器"""
        try:
            # 在连接时创建 Event，确保在正确的事件循环中
            self.hello_received = asyncio.Event()

            # 建立WebSocket连接 (兼容不同Python版本的写法)
            try:
                # 新的写法 (在Python 3.11+版本中)
                self.websocket = await websockets.connect(
                    uri=self.WEBSOCKET_URL, 
                    additional_headers=self.HEADERS
                )
            except TypeError:
                # 旧的写法 (在较早的Python版本中)
                self.websocket = await websockets.connect(
                    self.WEBSOCKET_URL, 
                    extra_headers=self.HEADERS
                )

            # 启动消息处理循环
            asyncio.create_task(self._message_handler())

            # 发送客户端hello消息
            hello_message = {
                "type": "hello",
                "version": 1,
                "transport": "websocket",
                "audio_params": {
                    "format": "opus",
                    "sample_rate": AudioConfig.INPUT_SAMPLE_RATE,
                    "channels": AudioConfig.CHANNELS,
                    "frame_duration": AudioConfig.FRAME_DURATION,
                }
            }
            await self.send_text(json.dumps(hello_message))

            # 等待服务器hello响应
            try:
                await asyncio.wait_for(
                    self.hello_received.wait(), 
                    timeout=10.0
                )
                self.connected = True
                logger.info("已连接到WebSocket服务器")
                return True
            except asyncio.TimeoutError:
                logger.error("等待服务器hello响应超时")
                if self.on_network_error:
                    self.on_network_error("等待响应超时")
                return False

        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            if self.on_network_error:
                self.on_network_error(f"无法连接服务: {str(e)}")
            return False

    async def _message_handler(self):
        """处理接收到的WebSocket消息"""
        try:
            async for message in self.websocket:
                if isinstance(message, str):
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type")
                        if msg_type == "hello":
                            # 处理服务器 hello 消息
                            await self._handle_server_hello(data)
                        else:
                            if self.on_incoming_json:
                                self.on_incoming_json(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"无效的JSON消息: {message}, 错误: {e}")
                elif self.on_incoming_audio:  # 使用 elif 更清晰
                    self.on_incoming_audio(message)

        except websockets.ConnectionClosed:
            logger.info("WebSocket连接已关闭")
            self.connected = False
            if self.on_audio_channel_closed:
                # 使用 schedule 确保回调在主线程中执行
                await self.on_audio_channel_closed()
        except Exception as e:
            logger.error(f"消息处理错误: {e}")
            self.connected = False
            if self.on_network_error:
                # 使用 schedule 确保错误处理在主线程中执行
                self.on_network_error(f"连接错误: {str(e)}")

    async def send_audio(self, data: bytes):
        """发送音频数据"""
        if not self.is_audio_channel_opened():  # 使用已有的 is_connected 方法
            #logger.warning('无法音频数据')
            return

        try:
            # logger.warning('发送音频数据')
            await self.websocket.send(data)
        except Exception as e:
            if self.on_network_error:
                logger.warning(f"发送音频数据失败: {str(e)}")
                self.on_network_error(f"发送音频数据失败: {str(e)}")

    async def send_text(self, message: str):
        """发送文本消息"""
        if self.websocket:
            try:
                logger.warning(f'发送文本数据{message}')
                await self.websocket.send(message)
            except Exception as e:
                await self.close_audio_channel()
                if self.on_network_error:
                    self.on_network_error(f"发送消息失败: {str(e)}")

    def is_audio_channel_opened(self) -> bool:
        """检查音频通道是否打开"""
        return self.websocket is not None and self.connected

    async def open_audio_channel(self) -> bool:
        """建立 WebSocket 连接
        
        如果尚未连接,则创建新的 WebSocket 连接
        Returns:
            bool: 连接是否成功
        """
        if not self.connected:
            return await self.connect()
        return True

    async def _handle_server_hello(self, data: dict):
        """处理服务器的 hello 消息"""
        try:
            # 验证传输方式
            transport = data.get("transport")
            if not transport or transport != "websocket":
                logger.error(f"不支持的传输方式: {transport}")
                return
            print("服务链接返回初始化配置", data)

            # 设置 hello 接收事件
            self.hello_received.set()

            # 通知音频通道已打开
            if self.on_audio_channel_opened:
                await self.on_audio_channel_opened()

            logger.info("成功处理服务器 hello 消息")

        except Exception as e:
            logger.error(f"处理服务器 hello 消息时出错: {e}")
            if self.on_network_error:
                self.on_network_error(f"处理服务器响应失败: {str(e)}")

    async def close_audio_channel(self):
        """关闭音频通道"""
        if self.websocket:
            try:
                await self.websocket.close()
                self.websocket = None
                self.connected = False
                if self.on_audio_channel_closed:
                    await self.on_audio_channel_closed()
            except Exception as e:
                logger.error(f"关闭WebSocket连接失败: {e}")