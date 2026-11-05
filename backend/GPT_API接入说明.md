# GPT API：你需要修改的位置

## 1. 填写 `backend/.env.ai`

本次已创建这个文件，并已使用你填写的当前配置通过真实出题和评分测试。以下为配置格式示例，不包含真实密钥：

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

本次按已安装的 OpenAI Python SDK 接口实现并测试了请求分支和完整多行 JSON 的读取。官方参考页在当前环境返回 403，未将它们当作本次在线核验依据；下面链接便于你接入时核对服务最新要求：

- https://platform.openai.com/docs/api-reference/responses/create
- https://platform.openai.com/docs/api-reference/chat/create

## 3. 改任务说明与结果约定

`backend/app/application/content.py` 的 `ContentService` 中：

- `generate()`：完整练习题、提示和参考答案。
- `evaluate()`：0–10 总分、各原子技能分数和有依据的评语。
- `propose_skill()`：技能说明、提示词配置和原子技能拆分。
- `optimize()`：针对指定原子技能生成练习建议。

结果模型位于 `backend/app/domain/models.py`；技能提案和优化建议的模型在 `application/content.py`。`validated()` 返回校验后的类型对象，评分还检查原子技能 ID 集合是否完整对应。当前使用 JSON 对象输出并在服务端做字段和范围校验。若要改成供应商严格 JSON Schema 模式，应同时核对该模型对 schema 的支持，保留服务端校验。

## 4. 验证

在当前工作区执行 `powershell -ExecutionPolicy Bypass -File ".\outputs\start-flash-training.ps1" -RestartBackend`，然后访问 `http://127.0.0.1:8001/api/health`。

`ai_configured=true` 仅表示配置项非空，不代表模型接口已经调用成功。再在页面进入一个技能，实际生成题目并提交答案，才完成真实模型联调。

当前服务商返回的模型 ID 是 `gpt-6.1-sol`，已修正原配置中的大小写。该服务商还要求使用 JSON 对象模式时在 `input` 内明确提到 JSON；客户端已补充兼容处理，并通过真实出题、评分和回归测试。

未配置时返回 503；密钥/权限问题、限流、调用失败、结果格式错误均明确报错。不会默认给 50/60 分或写入掌握度。日志不输出密钥、完整学生答案或上游错误正文。

模型评分本身仍需使用人工标注样本验证；数据库一致性测试不能代替教学质量评测。
