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
    echo "进程 '$PROCESS_NAME' 已经在运行。"
else
    echo "进程不存在，启动新进程。"

    # 启动进程
    nohup python "$SCRIPT_DIR/homing_pigeon_bot.py" "$TOKEN" "$YOUR_USER_ID" > /dev/null 2>&1 &
    sleep 2

    echo "进程 '$PROCESS_NAME' 已启动。"
fi

