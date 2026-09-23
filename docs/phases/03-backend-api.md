# Phase 3 后端接口实现

**状态**：已完成（2026-09-24）

**目标**：实现两轮管道与全部业务接口，每个高德接口都有契约测试，并完成字段核对。

## 任务清单

1. 坐标转换模块（GCJ-02 与 WGS-84 双向），对照现有双坐标表做 1 米级校验。
2. 高德客户端与错误码分类。
3. Key 池与限流（含每 20 次随机休息 3—8 秒、日配额护栏）。
4. 第一轮 POI 管道（断点续跑、配额暂停、匹配分档）。
5. 第二轮 AOI 管道（polyline 解析、球面面积、no_aoi 不重试）。
6. 任务、记录与导出接口（CSV、两份 GeoJSON）。
7. 真实冒烟脚本。
8. 接口字段核对（Task 3.8）：采集后端真实返回字段，与 openapi 声明和前端字段做差集，差异为零。

## 验收标准

- 全部接口有 pytest 覆盖，含错误路径、分页、筛选与导出解析断言。
- 高德接口的契约测试断言参数名正确（重点 `city_limit`／`page_num`），AOI 覆盖有数据、空、10012 三种响应。
- 冒烟脚本对三个已知样本输出 POI 与 AOI 结果，`infocode` 与耗时记入台账。
- `docs/field-parity.md` 差异为零且脚本已纳入 CI。

## 验收记录

**完成时间**：2026-09-24

**实现了什么**

- 坐标转换：`app/services/coord.py` 用迭代反解做 GCJ-02 与 WGS-84 双向转换。
- 几何：`app/services/geometry.py` 解析下划线坐标串并按球面公式算公顷面积。
- 调度：`app/services/keypool.py` 做 Key 轮换、禁用、日计数，`Pacer` 做全局 QPS 限制与「每 N 次随机休息」。
- 高德客户端：`app/services/amap_client.py` 封装搜索 POI 2.0、AOI 边界查询、地理编码，错误码统一走 `amap_errors`。
- 匹配分档：`app/services/matching.py` 输出 exact／contains／weak。
- 两轮管道：`pipeline_poi.py` 把每个名称展开成候选并落库，`pipeline_aoi.py` 对选中记录取面并算面积；都支持断点续跑与暂停。
- 导出：`export.py` 输出固定列顺序的 CSV 与两份 GeoJSON（WGS-84 与 GCJ-02）。
- 接口：新增 `POST /api/tasks/{id}/run`、`/aoi`、`/pause`、`/resume`、`GET /api/tasks/{id}/export`。
- 字段核对：`scripts/check_field_parity.py` 生成 `docs/field-parity.md`，缺失字段为 0。

**验收命令与结果**

| 命令 | 结果 |
|---|---|
| `uv run pytest -q` | 47 passed（新增 coord 3、geometry 3、keypool 4、matching 2、amap client 4、pipeline 5、export 3） |
| `npm test` | 6 个文件 12 passed |
| `npm run typecheck` | 通过 |
| `uv run python scripts/check_field_parity.py --strict` | 缺失字段 0，退出码 0 |
| `uv run python scripts/smoke_real.py --yes` | 真实调用：3 次 POI 搜索 + 2 次 AOI；AOI 返回 10012，任务按预期暂停并提示提工单 |

**真实接口实测（2026-09-24）**

| 名称 | 全部候选 | 分类码 11 开头 | 名称完全一致 |
|---|---|---|---|
| 越秀公园 | 25 | 15 | 1（B00140BNNF，110101） |
| 天河公园 | 25 | 9 | 1（B00140H465，110101） |

**与本计划的偏差**

- 新增 `poi_page_size`、`poi_max_pages`、`typecode_prefix` 三个设置：实测发现「保留全部候选」会把公园内部的墓、亭、地铁口一并收进来，一个名字最多 25 条且大部分是子点位。见 `decisions.md` D-013。
- AOI 权限不足时改为暂停任务并给出工单提示，而不是把每条记录都标成失败。见 D-014。
- 结果表默认只筛「名称完全一致」的候选。见 D-015。

**遗留项**

1. AOI 真实取面仍被权限阻塞（10012），Phase 4 只能验证到「暂停并提示」这一步。
2. 若清空匹配度筛选并全选，第二轮会发出上万次 AOI 请求，界面上只做了数量提示，没有硬上限。
