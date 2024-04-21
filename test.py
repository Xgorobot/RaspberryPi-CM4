import os

# 读取单个环境变量
your_variable_value = os.getenv("CLASH_PORT")

if your_variable_value is not None:
    print("Your variable value is:", your_variable_value)
else:
    print("Your variable is not set or has a None value.")


