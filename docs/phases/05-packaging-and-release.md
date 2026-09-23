# Phase 5 打包与发布

**状态**：已完成（2026-09-24）

**目标**：在四个阶段之外补上分发能力。同一个仓库发布两个版本——源码版给有 Python 环境的人，免安装版给只想双击就用的人。

## 任务清单

1. exe 启动器 `scripts/launcher.py`：冻结后把数据目录指向 exe 同级的 `data/`，延迟 3 秒自动打开浏览器，控制台窗口关闭即停止服务。
2. 冻结感知的静态目录解析：`app/main.py` 里 `resolve_dist()` 依次尝试 `sys._MEIPASS`、源码目录、exe 同级目录，找到含 `index.html` 的那个。
3. 打包脚本 `scripts/build_exe.py`：PyInstaller `--onedir` 打包，随后生成两个 zip。
4. 发布产物：
   - `dist/amap-poi-aoi-0.1.0-win64.zip`：免安装版，含 `amap-poi-aoi.exe`、`_internal/`、`frontend/dist/`、`data/` 与中文使用说明。
   - `dist/amap-poi-aoi-0.1.0-source.zip`：源码版，按 `git ls-files` 导出，不含 exe。
5. `.gitignore` 增加 `dist/` 与 `build/`，产物走 Release 附件而不是提交进仓库。

## 验收记录

| 检查 | 结果 |
|---|---|
| PyInstaller 构建 | 成功（`--onedir`，含 uvicorn 相关 hidden import） |
| exe 实测启动 | `health` 200、前端页面 200（457 字节 index.html） |
| exe 数据目录 | 首次运行自动在 exe 同级创建 `data/`，配置与数据库都落在那里 |
| 免安装包体积 | 22.8 MB |
| 源码包体积 | 0.2 MB |
| 测试套件 | 51 passed（打包未破坏任何既有行为） |

## 与计划的关系

Phase 5 不在原来的四阶段计划里。它是在 Phase 4 完成后为支持分发而追加的，因此单独成篇，不改动前四阶段的验收记录。

## 遗留项

1. exe 未做代码签名，Windows SmartScreen 首次运行可能提示「未知发布者」。
2. 只打了 Windows x64；macOS 与 Linux 未打包（PyInstaller 需要在对应系统上构建）。
3. 仓库尚未配置 remote，CI 与 Release 上传都还没在 GitHub 上真实执行过。
