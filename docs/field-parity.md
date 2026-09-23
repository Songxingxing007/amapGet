# 字段对账报告

由 `scripts/check_field_parity.py` 生成，规则是「后端运行时真实返回的字段为准」。
前端如果引用了下表 `缺失` 列里的字段，必须先改后端或改前端。

| 接口 | 运行时字段 | 缺失 |
|---|---|---|
| GET /api/config | daily_limit_per_key, default_region, key_count, keys_masked, poi_max_pages, poi_page_size, qps, sleep_every, sleep_max_seconds, sleep_min_seconds, typecode_prefix | - |
| POST /api/tasks/preview | columns, name_confidence, row_count_preview, rows, suggested_adname_column, suggested_name_column | - |
| POST /api/tasks | skipped, task_id, total | - |
| GET /api/tasks/{id} | done, failed, id, kind, paused_reason, source_filename, status, total | - |
| GET /api/records | ids, items, page, page_size, total | - |
| GET /api/records -> items[] | address, adname, aoi_area_ha, aoi_status, id, lat_gcj02, lat_wgs84, lng_gcj02, lng_wgs84, match_level, poi_id, poi_name, poi_type, query_name, selected, task_id, typecode | - |
| GET /api/tasks/{id}/export (csv header) | query_name, match_level, poi_name, poi_id, poi_type, typecode, address, adname, lng_gcj02, lat_gcj02, lng_wgs84, lat_wgs84, aoi_status, aoi_area_ha | - |

## 结论

- 缺失字段总数：0
- `POST /api/config/verify` 与 `POST /api/tasks/{id}/run`、`/aoi`、`/pause`、`/resume` 需要真实网络或后台任务，不在本报告里采集，字段以 openapi.json 为准。
