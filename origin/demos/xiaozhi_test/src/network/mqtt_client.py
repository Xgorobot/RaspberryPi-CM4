# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt


class MqttClient:
    def __init__(
        self, server, port, username, password, subscribe_topic, publish_topic=None,
        client_id="PythonClient", on_connect=None, on_message=None, 
        on_publish=None, on_disconnect=None
    ):
        """
        初始化 MqttClient 实例。

        :param server: MQTT 服务器地址
        :param port: MQTT 服务器端口
        :param username: 登录用户名
        :param password: 登录密码
        :param subscribe_topic: 订阅的主题
        :param publish_topic: 发布的主题
        :param client_id: 客户端 ID，默认为 "PythonClient"
        :param on_connect: 自定义的连接回调函数
        :param on_message: 自定义的消息接收回调函数
        :param on_publish: 自定义的消息发布回调函数
        :param on_disconnect: 自定义的断开连接回调函数
        """
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.subscribe_topic = subscribe_topic
        self.publish_topic = publish_topic
        self.client_id = client_id

        # 创建 MQTT 客户端实例，使用最新的API版本
        self.client = mqtt.Client(
            client_id=self.client_id, protocol=mqtt.MQTTv5
        )

        # 设置用户名和密码
        self.client.username_pw_set(self.username, self.password)

        # 设置回调函数，如果提供了自定义回调函数，则使用自定义的，否则使用默认的
        if on_connect:
            self.client.on_connect = on_connect
        else:
            self.client.on_connect = self._on_connect
            
        self.client.on_message = on_message if on_message else self._on_message
        self.client.on_publish = on_publish if on_publish else self._on_publish
        
        if on_disconnect:
            self.client.on_disconnect = on_disconnect
        else:
            self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """默认的连接回调函数。"""
        if rc == 0:
            print("✅ 成功连接到 MQTT 服务器")
            # 连接成功后，自动订阅主题
            client.subscribe(self.subscribe_topic)
            print(f"📥 已订阅主题：{self.subscribe_topic}")
        else:
            print(f"❌ 连接失败，错误码：{rc}")

    def _on_message(self, client, userdata, msg):
        """默认的消息接收回调函数。"""
        topic = msg.topic
        content = msg.payload.decode()
        print(f"📩 收到消息 - 主题: {topic}，内容: {content}")

    def _on_publish(self, client, userdata, mid, properties=None):
        """默认的消息发布回调函数。"""
        print(f"📤 消息已发布，消息 ID：{mid}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        """默认的断开连接回调函数。"""
        print("🔌 与 MQTT 服务器的连接已断开")

    def connect(self):
        """连接到 MQTT 服务器。"""
        try:
            self.client.connect(self.server, self.port, 60)
            print(f"🔗 正在连接到服务器 {self.server}:{self.port}")
        except Exception as e:
            print(f"❌ 连接失败，错误: {e}")

    def start(self):
        """启动客户端并开始网络循环。"""
        self.client.loop_start()

    def publish(self, message):
        """发布消息到指定主题。"""
        result = self.client.publish(self.publish_topic, message)
        status = result.rc
        if status == 0:
            print(f"✅ 成功发布到主题 `{self.publish_topic}`")
        else:
            print(f"❌ 发布失败，错误码：{status}")

    def stop(self):
        """停止网络循环并断开连接。"""
        self.client.loop_stop()
        self.client.disconnect()
        print("🛑 客户端已停止连接")


