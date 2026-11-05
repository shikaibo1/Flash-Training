# Backend: Prepare Development Environment (快速指南)

This document explains how to prepare the backend development environment: create a Python virtual environment, install Python dependencies, install system FFmpeg required by `pydub`, and run the API server and tests.

---

## 1. Create & activate virtual environment

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# If execution policy blocks you, run as admin: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Windows (cmd.exe):
```cmd
python -m venv .venv
.\.venv\Scripts\activate
```

macOS / Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

---

## 2. Install Python dependencies

From project root (or `backend/`):
```bash
pip install -r backend/requirements.txt
```

Notes:
- If you have multiple Python installations: `python -m pip install -r backend/requirements.txt`.
- After installation you can run quick checks like `python -c "import fastapi, uvicorn, pydantic, speech_recognition, pydub; print('OK')"` to verify imports.

---

## 3. Install FFmpeg (required by `pydub` for audio processing)

Windows (recommended installers):
- Chocolatey: `choco install ffmpeg`
- Scoop: `scoop install ffmpeg`
- Winget: `winget install gyan.ffmpeg`

macOS:
- Homebrew: `brew install ffmpeg`

Ubuntu / Debian:
- `sudo apt update && sudo apt install ffmpeg`

Verify:
```bash
ffmpeg -version
```
Make sure `ffmpeg` is in your PATH.

---

## 4. Environment variables

Copy or create a `.env` file at project root or `backend/.env` and set keys used by the backend (examples):
```
ARK_API_KEY=your_key_here
ARK_BASE_URL=... (if using Doubao)
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## 5. Run backend server

From project root:
```bash
uvicorn backend.api_server:app --reload --port 8000
```

The API base is `http://localhost:8000/api` by convention in the frontend `.env`.

---

## 6. Run tests & linters

Run tests:
```bash
pytest -q
```

Lint (if configured):
```bash
flake8
```

---

## 7. Troubleshooting

- `ImportError` after pip install: ensure your virtualenv is activated, and you installed into the same interpreter used to run the server.
- `ffmpeg` not found: verify `ffmpeg -version` works in the same terminal used to run the server.
- If uploads/transcription fail, check `backend/logs` and server console for tracebacks.

---

## 8. Optional: Docker & CI

If you use Docker/CI, ensure `ffmpeg` and the dependencies in `backend/requirements.txt` are included in the image and that environment variables are provided to the container.

---

If you want, I can also add a `Makefile` or a cross-platform script (PowerShell + bash) to automate setup steps. Let me know which you'd prefer.

---

中文版（简体中文）

# 后端：准备开发环境（快速指南）

本文件说明如何准备后端开发环境：创建 Python 虚拟环境、安装 Python 依赖、安装 `pydub` 依赖的系统级 `ffmpeg`，并运行 API 服务与测试。

---

## 1. 创建并激活虚拟环境

Windows（PowerShell）：
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# 如果执行策略阻止，请以管理员运行：Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Windows（cmd.exe）：
```cmd
python -m venv .venv
.\.venv\Scripts\activate
```

macOS / Linux：
```bash
python -m venv .venv
source .venv/bin/activate
```

---

## 2. 安装 Python 依赖

在项目根目录（或 `backend/`）运行：
```bash
pip install -r backend/requirements.txt
```

提示：
- 如果系统有多个 Python 版本，使用 `python -m pip install -r backend/requirements.txt` 确保安装到目标解释器。
- 安装完成后可运行快速导入检查：
```bash
python -c "import fastapi, uvicorn, pydantic, speech_recognition, pydub; print('OK')"
```

---

## 3. 安装 FFmpeg（`pydub` 依赖）

Windows（推荐方式）：
- Chocolatey: `choco install ffmpeg`
- Scoop: `scoop install ffmpeg`
- Winget: `winget install gyan.ffmpeg`

macOS：
- Homebrew: `brew install ffmpeg`

Ubuntu / Debian：
- `sudo apt update && sudo apt install ffmpeg`

验证：
```bash
ffmpeg -version
```
确保 `ffmpeg` 在系统 PATH 中。

---

## 4. 环境变量

在项目根或 `backend/` 创建 `.env` 文件并设置后端需要的环境变量（示例）：
```
ARK_API_KEY=your_key_here
ARK_BASE_URL=...  # 如果使用 Doubao
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## 5. 启动后端服务

在项目根目录运行：
```bash
uvicorn backend.api_server:app --reload --port 8000
```

默认前端与文档中约定的 API 基址为 `http://localhost:8000/api`。

---

## 6. 运行测试与代码检查

运行测试：
```bash
pytest -q
```

运行 linter（如已配置）：
```bash
flake8
```

---

## 7. 故障排查

- 如果在 `pip install` 后出现 `ImportError`：确认虚拟环境已激活，并且依赖安装到了运行时使用的解释器。
- `ffmpeg` 找不到：在同一终端运行 `ffmpeg -version` 验证是否可用。
- 如果上传或转写失败：检查 `backend/logs` 和后端控制台输出获取堆栈信息。

---

## 8. 可选：Docker 与 CI

如果在容器或 CI 中运行，请确保 Docker 镜像或 CI 环境包含 `ffmpeg`，并将 `backend/requirements.txt` 中的依赖安装到镜像内，同时为容器提供必要的环境变量。

---

如果需要，我也可以为你添加自动化脚本（例如 `Makefile`、跨平台的 PowerShell + bash 脚本）来简化环境准备流程，请告诉我你偏好哪种方式。