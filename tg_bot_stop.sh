#!/bin/bash

# 此处替换为你的机器人Token
TOKEN=""
# 此处替换为你的用户ID
YOUR_USER_ID=""

# 获取脚本的绝对路径
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROCESS_NAME="python "$SCRIPT_DIR/homing_pigeon_bot.py" "$TOKEN" "$YOUR_USER_ID""

# 使用 pgrep 查找进程是否存在
if pgrep -f "$PROCESS_NAME" > /dev/null; then
    echo "进程 '$PROCESS_NAME' 在运行。"
    pkill -f "$PROCESS_NAME"
    echo "进程 '$PROCESS_NAME' 已终止，机器人停止运行。"
    sleep 1
else
    echo "进程 '$PROCESS_NAME' 不存在，机器人不在运行，无需停止。"

fi

