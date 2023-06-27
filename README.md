# 简介

> easy_chat：基于gpt的聊天机器人

![](example.png)

# 快速开始


### 一.运行环境

支持各主流操作系统

先安装 `Python`
> 建议Python版本3.8.x，尤其是需要进行exe打包时（3.8为win7上可运行的最后一个python版本）

创建虚拟环境并激活后，安装所需核心依赖：

```bash
python -m venv venv
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 二.相关配置
1. 根据需要，修改config.py文件中的：DEBUG = True

2. 根据config-template.json文件创建config.json：

```bash
# config.json文件内容示例
{
  "openai": {
    "open_ai_proxy": {  # openai国内代理商家，免翻墙
      "api_base": "https://xxx/v1",
      "api_key": "xxx"
    },
    "open_ai_chat_model": "gpt-3.5-turbo",
    "max_tokens": 4000,
    "openai_retry": {  # openai接口失败时重试的参数
      "min_wait": 3,
      "max_wait": 5,
      "max_attempt_number": 3
    },
    "open_ai_system_prompt": [
      {
        "role": "system",
        "content": "你是个乐于助人的助手。"
      }
    ]
  }
}
```

### 三.运行
**本地：**
```bash
python app.py
```
**线上（简单场景）：** 
```bash
nohup python app.py >> ./out.log 2>&1 & echo $! > ./pidfile
```
### 四.运行结果示例
![](example.png)
