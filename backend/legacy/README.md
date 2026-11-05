# 历史实现（不参与运行）

这里保留重构前的 API、JSON 文件管理器、豆包客户端和旧命令行程序，便于对照。
新版入口为 `backend/app/main.py`；所有业务读写均通过 SQLite。

不要从这里启动应用。旧源码的相对导入和目录结构仅作为历史参考，不保证可以独立执行。
原始数据仍在 `backend/data/*.json` 与 `backend/backend/data/`，只供首次迁移读取。
