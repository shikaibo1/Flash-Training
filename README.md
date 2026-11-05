# Flash Training

React + TypeScript 前端、FastAPI 后端、SQLite 数据库。保留技能库、文字练习、历史回放和掌握度页面，已完成数据库改造及后续业务分层重构。

## 运行

开发机器可使用外部工作区的 `outputs/start-flash-training.ps1`；该脚本依赖开发机器目录，不属于仓库的通用启动方式。克隆仓库后按下面步骤启动。

在另一台机器上，从 `backend/` 目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.lock
Copy-Item .env.ai.example .env.ai
python -m uvicorn api_server:app --host 127.0.0.1 --port 8001
```

从 `frontend/` 目录执行：

```powershell
npm ci
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1
```

需要 Python 3.10+、Node.js 22.12+。本次在 Python 3.12 和 Node.js 24 下验证。前端默认访问 `http://localhost:8001/api`。模型未配置时，仍可浏览技能库和历史，生成/评估会明确报错。

macOS/Linux 使用 `source .venv/bin/activate` 激活后端环境，使用 `cp` 代替上面的 `Copy-Item`。前端页面默认地址为 http://localhost:5173/，接口文档为 http://127.0.0.1:8001/docs。

## 公开仓库中的内容

包含完整前后端源码、原后端存档 `backend/legacy/`、依赖锁文件、测试、配置示例、文档和初始技能定义。首次启动会创建自己的 SQLite 数据库并导入初始定义。

实际 API 密钥、用户答案与成绩、历史档案、数据库、录音、备份、依赖目录和构建缓存由 `.gitignore` 排除，保留在本地。配置请从 `backend/.env.ai.example` 和 `frontend/.env.example` 复制。`backend/legacy/` 仅作源码参照，当前运行入口是 `backend/api_server.py`。

当前 Windows 运行环境中 Vite 默认配置加载会遇到目录权限问题，可用：

```powershell
npm run build
npm run preview -- --host 127.0.0.1 --port 5173
```

## GPT API 修改位置

1. **配置文件：`backend/.env.ai`**，填写 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`。模型使用自己账号可访问的 ID，代码不替你选定。
2. **调用实现：`backend/app/infrastructure/ai.py`**，搜索 `GPT API EDIT POINT`。支持 Responses 和 Chat Completions 两种方式。
3. **具体任务：`backend/app/application/content.py`**，包含出题、评估、自定义技能拆分及优化建议的任务说明。

修改配置后重启后端。完整说明见 [GPT API 接入说明](backend/GPT_API接入说明.md)。旧 `backend/.env` 中的豆包配置不再读取；已有文件保留供你参考。

## 代码结构

```text
backend/
  api_server.py             # 兼容旧启动方式的入口
  app/
    main.py                 # 应用工厂、启动迁移、错误处理
    settings.py             # 配置，按绝对目录定位
    api/                    # HTTP 路由，按技能/练习/进度划分
    bootstrap.py            # 显式组装各服务与依赖
    domain/                 # 领域数据、命令、规则、仓库和事务协议
      models.py             # 技能、会话、成绩、进度等明确类型
      commands.py           # 输入数据约束
      learning.py           # 不访问数据库的掌握度与时间规则
      ports.py              # 应用依赖的协议
    application/            # 业务用例；无 SQL、HTTP、SDK 依赖
      skills.py             # 技能和原子技能配置
      practice.py           # 出题、会话、提交、恢复
      progress.py           # 得分、自评、掌握度、推荐
      records.py            # 回放记录、档案与统计
      learning.py           # 在调用者事务内记录学习表现
      content.py            # 模型任务、结果校验
    infrastructure/
      repositories/         # 技能、练习、进度、用户的专用 SQL 仓库
      unit_of_work.py       # 所有仓库共享事务；统一提交/回滚
      database.py           # 表结构、连接、版本与只读保护
      serialization.py      # 数据库 JSON 编解码约定
      legacy_import.py      # 旧 JSON 一次性迁移
      ai.py                 # 唯一外部模型调用适配器
    manage.py               # 迁移、检查、数据库备份
  tests/                    # 不使用真实模型的测试
  data/                     # SQLite 数据库、原始 JSON、迁移备份
  legacy/                   # 原后端源码存档，不参与运行
frontend/src/
  lib/api.ts                # 后端请求与类型、错误处理
  pages/PracticeSession.tsx # 会话恢复、答题、提交、结果
```

职责与扩展方法见 [架构说明](backend/架构说明.md)，表结构和迁移见 [后端说明](backend/README.md)。原通用 `TrainingService` 和 `Repository` 已移除，运行时使用上述独立服务与仓库。

## 验证

后端：在 `backend/` 执行 `python -m unittest discover -s tests -v`。

本轮验证：44 项后端测试、7 项前端测试通过；类型检查和构建通过，ESLint 为 0 错误、6 个既有 UI 热更新警告。运行中比较了 120 份重构前后的只读接口响应，已有字段和值保持一致；数据库结构仍为 v1，现有数据保留。

前端：在 `frontend/` 执行 `npm run typecheck`、`npm test`、`npm run lint` 和 `npm run build`。前端测试包括真实评分面板渲染、缺失维度处理、统计和存储异常。

当前是绑定本机的学习工具，尚未实现账号认证。`user_id` 用于数据区分，不能当作登录身份校验；前端仍使用 `default_user`。
