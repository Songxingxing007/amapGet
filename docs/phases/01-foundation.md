# Phase 1 前后端基础框架

**状态**：已完成（2026-09-23）

**目标**：搭好前后端骨架并能跑测试，为后续阶段提供可验证的底座。

## 任务与结果

| 任务 | 内容 | 状态 |
|---|---|---|
| 1.1 | 安装 uv、初始化项目、装依赖 | 完成 |
| 1.2 | FastAPI 健康检查与测试 | 完成 |
| 1.3 | Vue3 骨架、后端托管静态站点 | 完成 |
| 1.4 | 配置读写接口（Key 打码、配额与休息参数） | 完成 |
| 1.5 | SQLite 模型（Task／Record／KeyState） | 完成 |
| 1.6 | CI 工作流（后端 pytest、前端类型检查与构建） | 完成 |
| 额外 | 第三方接口联通探针 `/api/config/verify` 与错误码分类 | 完成 |

## 验收证据

- 后端：`uv run pytest -q` → 11 passed（health 1、config 3、models 1、错误码 2、verify 4）
- 前端：`npm test` → 1 passed；`npm run typecheck` 通过；`npm run build` 产出 `dist/`（index.html 0.45 kB、css 364 kB、js 980 kB）
- 整合：启动 uvicorn 后 `GET /api/health` → 200 `{"status":"ok"}`；`GET /` → 200 返回前端页面
- 第三方真实探针：geocode `infocode=10000`、POI 两个样本均命中 110101 公园分类、AOI `infocode=10012`（无权限，符合预期）
- 提交：`chore: bootstrap uv project with fastapi health endpoint`、`feat: vue3 skeleton with health check, served by fastapi`、`feat: config api with masked keys, quota and sleep settings`、`feat: sqlite models for tasks and records, ci workflow`

## 与计划的偏差

- 前端与后端字段契约尚未落地：本阶段只有 health／config／verify 三个接口，OpenAPI 生成类型按计划放在 Phase 2。
- CI 只在本地等价验证过（本机未推送到 GitHub），真正跑通要等仓库推送后。

## 遗留项

1. AOI 权限未开通（10012），Phase 3 的 AOI 部分只能用打桩测试，真实联调等工单。
2. 前端打包体积 980 kB（Element Plus 全量引入），Phase 4 可做按需引入或代码分割。
3. MCP Server 已写入 `config.toml`，需重启应用生效。
