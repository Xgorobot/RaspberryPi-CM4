APPId = "204e2232"
APIKey = "1896d14df5cd043b25a7bc6bee426092"
APISecret = "MDJjYzQ3NmJmODY2MmVlMDdhMDdlMjA2"
# 请求数据
request_data = {
    "header": {
        "app_id": "123",
        "status":0
    },
    "parameter": {
        "oral": {
            "oral_level": "mid",
            "spark_assist": 1,
            "scenarized": 0
        },
        "tts": {
            "vcn": "x4_lingxiaoxuan_oral",
            "volume": 50,
            "speed": 50,
            "pitch": 50,
            "bgs": 0,
            "rhy": 0,
            "audio": {
                "encoding": "lame",
                "sample_rate": 16000,
                "channels": 1,
                "bit_depth": 16,
                "frame_size": 0
            },
            "pybuf": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "plain"
            }
        }
    },
    "payload": {
        "text": {
            "encoding": "utf8",
            "compress": "raw",
            "format": "plain",
            "status": 0,
            "seq": 0,
            "text": "spark_tts.txt"
        }, 
        "user_text": {
            "encoding": "utf8",
            "compress": "raw",
            "format": "plain",
            "status": 0,
            "seq": 0,
            "text": "spark_tts.txt"
        }
    }
}

# 请求地址
request_url = "ws://cbm01.cn-huabei-1.xf-yun.com/v1/private/medd90fec"

# 用于快速定位响应值

response_path_list = ['$..payload.pybuf', '$..payload.audio', ]