# Phase 2 前端 UI

**状态**：已完成（2026-09-23）

**目标**：在 mock 数据下把配置、上传、进度、结果四个页面做出来，并通过组件测试与类型契约。

## 任务清单

1. 路由与页面骨架（配置／上传／结果）。
2. API 客户端与类型定义，接入 openapi.json 生成的类型。
3. 配置页：Key 池增删、QPS、日配额、休息参数，保存后回显打码 Key。
4. 上传页：CSV 与 xlsx 拖拽上传、列识别与手选、表头预览。
5. 任务进度组件：轮询、计数、暂停原因与暂停／继续。
6. 结果表格：匹配度／行政区／关键词／是否有 AOI 多条件筛选、跨页批量勾选、导出下拉。

## 验收标准

- 每个页面与组件的 vitest 通过，覆盖批量勾选与全选筛选结果逻辑。
- `npm run typecheck` 通过（类型来自 openapi.json）。
- 用真实测试文件 `sample.xlsx`（12 行 × 11 列，名称列「公园名称」）做列识别快照测试，识别结果正确。
- 与 health／config／verify 三个已实现接口做一次真实联调（不消耗高德配额）。

## 验收记录

**完成时间**：2026-09-23

**实现了什么**

- 路由与页面骨架：`/config`、`/upload`、`/result/:taskId`，顶栏菜单加后端连通状态。
- API 客户端与类型：`openapi.json` 由后端导出（`scripts/export_openapi.py`），前端用 `npm run gen:api` 生成 `src/api/schema.d.ts`，`src/api/types.ts` 只做别名。
- 配置页：Key 池增删、QPS、单 Key 日上限、默认城市、休息次数与区间；保存后回显打码 Key；「测试接口」调 `/api/config/verify` 显示 Key／地理编码／AOI 三段结果。
- 上传页：CSV 与 xlsx 拖拽上传，调 `/api/tasks/preview` 识别列并预览，名称列与行政区列可手动改，创建任务后跳到结果页。
- 进度组件：每 2 秒轮询 `/api/tasks/{id}`，终态停止，显示暂停原因。
- 结果表格：匹配度／行政区／关键词／AOI 状态筛选、分页、跨页勾选、全选筛选结果、对选中项取 AOI、导出下拉（CSV 与两种坐标系 GeoJSON）。

**验收命令与结果**

| 命令 | 结果 |
|---|---|
| `uv run pytest -q` | 22 passed（新增 ingest 3、tasks 5、records 3） |
| `npm test` | 6 个文件 11 passed |
| `npm run typecheck` | 通过 |
| `npm run build` | 通过（js 约 1.0 MB，提示可做代码分割） |
| 端到端（起服务后用真实 `sample.xlsx`） | preview 识别 11 列、建议名称列「公园名称」置信度 header；创建任务 12 条、跳过 0；记录列表 12 条且行政区正确；根路径 200 |

**与本计划的偏差**

- 列识别放在后端（`app/services/ingest.py`）而不是前端 FileReader：xlsx 也要支持，且同一套规则供预览与建任务复用，避免两份实现。见 `decisions.md` D-011。
- 任务与记录接口提前到本阶段实现（原计划属 Phase 3）：否则上传页、进度组件、结果表格没有真实接口可测。真正的采集管道仍在 Phase 3。
- 前端新增 `.npmrc`（`legacy-peer-deps=true`）：TypeScript 6 与 openapi-typescript 的 peer 范围冲突。见 `decisions.md` D-012。

**遗留项**

1. `runAoi` 调用的 `/api/tasks/{id}/aoi` 尚未实现（Phase 3），当前点击会显示后端返回的错误信息。
2. 导出接口同样属 Phase 3，导出下拉现在会打开一个 404 链接。
3. 前端包体约 1 MB，Phase 4 再考虑 Element Plus 按需引入。
