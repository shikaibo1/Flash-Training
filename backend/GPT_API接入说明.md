# GPT API：你需要修改的位置

## 1. 填写 `backend/.env.ai`

从 `.env.ai.example` 复制配置并填写自己的账号信息。此次职业能力重构未调用真实模型，以下示例不包含真实密钥：

```dotenv
OPENAI_API_KEY=填写你自己的密钥
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=填写你账号可访问的模型ID
AI_API_STYLE=responses
AI_TIMEOUT_SECONDS=60
```

官方 OpenAI 使用 `responses`。如果你使用的代理或兼容服务只支持 Chat Completions，则填写该服务的兼容地址，并设置：

```dotenv
AI_API_STYLE=chat_completions
```

地址通常包含 `/v1`，不要填写到 `/responses` 或 `/chat/completions` 这一层。能否访问某个模型取决于你自己的账号和服务，不在代码里猜测。

环境变量优先于 `.env.ai`。修改文件后重启后端；同名系统环境变量会覆盖文件值。原 `.env` 的 `ARK_*` 配置不再加载。不要把密钥放入 `frontend/.env` 或任何 `VITE_*` 变量，它们会进入浏览器构建产物。

## 2. 找到唯一调用文件 `backend/app/infrastructure/ai.py`

搜索以下标记：

- `GPT API EDIT POINT A`：SDK 客户端、密钥、地址、超时和重试次数。
- `GPT API EDIT POINT B`：`client.responses.create(...)`，默认方式。
- `GPT API EDIT POINT C`：`client.chat.completions.create(...)`，兼容方式。

业务层只需要 `generate_json(task, payload)`，所以更换供应商不必修改数据库或路由。

沿用项目已有的两个 SDK 请求分支。此次未安装依赖或运行验证；下面链接便于你接入时核对服务要求：

- https://platform.openai.com/docs/api-reference/responses/create
- https://platform.openai.com/docs/api-reference/chat/create

## 3. 改任务说明与结果约定

`backend/app/application/content.py` 的 `ContentService` 中：

- `generate()`：根据任务和目标原子生成完整模拟材料、提示和参考答案。
- `evaluate()`：逐原子取证，检查答案原文引用，再按可观察项等权计算总分。
- `propose_task()`：为自定义目标组合已有原子，明确拒绝未知 ID 和不匹配情境。
- `application/evidence.py` 的 `recommendations()`：基于情境证据和先修关系推荐，不调用模型。

结果模型位于 `backend/app/domain/models.py`；任务提案模型在 `application/content.py`。`validated()` 返回校验后的类型对象，评分还检查本次目标原子是否恰好各出现一次、非零分是否有答案引用。当前使用 JSON 对象输出并在服务端做字段和范围校验。

## 4. 验证

在 `backend/` 激活已有 Python 环境后执行 `python -m uvicorn api_server:app --host 127.0.0.1 --port 8001`，然后访问 `http://127.0.0.1:8001/api/health`。使用新数据库 `data/flash_training_v2.sqlite3`；已有 `.env.ai` 若设置了旧路径，需先调整。

`ai_configured=true` 仅表示配置项非空，不代表模型接口已经调用成功。再在页面进入一个技能，实际生成题目并提交答案，才完成真实模型联调。

配置中的模型 ID 由用户账号决定。开发协作使用的子 Agent 模型不自动改变应用运行时模型。真实出题和评分可能产生模型费用，并保存本地练习数据。

未配置时返回 503；密钥/权限问题、限流、调用失败、结果格式错误均明确报错。失败不会写入成绩或能力证据。日志不输出密钥、完整学生答案或上游错误正文。

模型评分本身仍需使用人工标注样本验证；数据库一致性测试不能代替教学质量评测。

未执行测试，由用户自行验证。
