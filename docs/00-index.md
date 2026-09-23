# amap-poi-aoi 文档索引

这是唯一需要长期维护的入口文档。每个阶段结束时更新本页的状态表，并在对应的阶段文档里写验收记录。

## 项目一句话

上传含名称列的 CSV 或 Excel，第一轮批量查高德 POI 候选（全部保留），界面多条件筛选后第二轮取 AOI 边界，导出 CSV 与两份 GeoJSON（WGS-84 与 GCJ-02）。

## 文档结构

| 文档 | 作用 | 维护时机 |
|---|---|---|
| `docs/00-index.md` | 进度看板与维护规则（本文件） | 每阶段结束时 |
| `docs/phases/01-foundation.md` | Phase 1 前后端基础框架 | 阶段进行中与结束时 |
| `docs/phases/02-frontend-ui.md` | Phase 2 前端 UI | 同上 |
| `docs/phases/03-backend-api.md` | Phase 3 后端接口 | 同上 |
| `docs/phases/04-integration.md` | Phase 4 前后端联调 | 同上 |
| `docs/phases/05-packaging-and-release.md` | Phase 5 打包与发布（追加） | 同上 |
| `docs/api-notes.md` | 外部接口台账与实测记录 | 每次真实调用后 |
| `docs/decisions.md` | 决策记录（含理由与时间） | 每做一个决定 |

## 阶段状态

| 阶段 | 状态 | 完成标志 | 验收记录 |
|---|---|---|---|
| Phase 1 前后端基础框架 | 已完成 | pytest 全绿、前端构建通过、`/api/health` 与根路径可访问 | `phases/01-foundation.md` |
| Phase 2 前端 UI | 已完成 | 四个页面接通真实后端接口，前端 11 个测试、类型检查与构建通过 | `phases/02-frontend-ui.md` |
| Phase 3 后端接口 | 已完成 | 全部接口有测试，字段核对差异为零，第三方接口契约测试通过 | `phases/03-backend-api.md` |
| Phase 4 前后端联调 | 已完成 | 全链路跑通，异常路径可控，README 三步可跑 | `phases/04-integration.md` |
| Phase 5 打包与发布 | 已完成 | exe 实测可启动，源码版与免安装版两个压缩包就绪 | `phases/05-packaging-and-release.md` |

## 每阶段的硬性门槛

1. 后端接口测试：pytest 覆盖本阶段新增或修改的全部接口。
2. 前端接口与组件测试：vitest 覆盖前端 API 客户端与页面交互。
3. 第三方接口测试：高德接口的契约测试（打桩）加每阶段 5—10 次真实调用，结果记入 `docs/api-notes.md`；能用 MCP 交叉验证的用 MCP 复核。
4. 字段准绳：接口字段以后端真实返回为准，前端类型由 `openapi.json` 生成，进入联调前必须跑字段核对脚本且差异为零。

## 快速命令

```bash
uv sync
uv run uvicorn app.main:app --app-dir backend --port 8000
uv run pytest -q
cd frontend && npm ci && npm test && npm run build
```
