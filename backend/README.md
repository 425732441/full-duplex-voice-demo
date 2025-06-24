# 后端服务说明

## 简介

本后端基于 FastAPI 框架，提供 WebSocket 及 HTTP 接口，支持语音识别（ASR）、语音合成（TTS）、大语言模型（LLM）对话等多模态智能对话能力。主要用于与前端进行实时音频、文本交互。

## 主要文件说明

- `server.py`：FastAPI 启动入口，提供 WebSocket `/ws` 及 HTTP `/connect` 接口，负责服务生命周期管理和跨域配置。
- `bot_fast_api.py`：核心业务逻辑，集成了语音识别（AssemblyAI）、语音合成（Cartesia）、大模型（OpenRouter/OpenAI）、上下文管理等多种能力，通过流水线方式处理音频和文本数据。
- `requirements.txt`：依赖包列表，包含所有运行本项目所需的 Python 库。

## 依赖环境

- Python 3.10 及以上
- 主要依赖：
  - `fastapi`
  - `uvicorn`
  - `python-dotenv`
  - `pipecat-ai` 及其扩展（assemblyai, openai, cartesia, silero, daily, webrtc）
  - `pipecat-ai-small-webrtc-prebuilt`

## 快速启动

1. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量（可在 `.env` 文件中设置相关 API Key）：

   - `ASSEMBLYAI_API_KEY`
   - `CARTESIA_API_KEY`
   - `OPENROUTER_API_KEY`
   - 其他相关配置

3. 启动服务：

   ```bash
   python server.py
   ```

   默认监听端口为 `7860`。

## 接口说明

- **WebSocket `/ws`**  
  用于前端与后端的实时音频/文本交互。

- **POST `/connect`**  
  返回 WebSocket 连接地址，便于前端动态获取。

## 其他说明

- 支持跨域请求，方便前后端分离部署。
- 详细业务逻辑和流水线处理请参考 `bot_fast_api.py`。
