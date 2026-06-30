# 长沙中考录取预测系统

这是一个面向长沙中考志愿填报场景的录取预测工具。系统以位次为核心依据，结合 2025 年录取数据和 2026 年新增/扩建学位信息，输出“冲、稳、保”参考学校。

预测结果仅供志愿填报参考，不构成录取承诺；实际录取以长沙市教育局最终公布为准。

## 技术栈

- Python 标准库 HTTP 服务
- SQLite 本地数据库
- 原生 HTML / CSS / JavaScript
- 无前端构建步骤
- 当前无第三方 Python 依赖

## 目录结构

```text
.
├── app.py                 # HTTP 服务入口
├── config.py              # 环境变量与路径配置
├── database.py            # 数据库初始化和基础数据
├── prediction_engine.py   # 预测算法
├── static/                # 前端页面、脚本、样式
├── data/                  # SQLite 数据库
├── logs/                  # 运行日志目录
├── scripts/check.py       # 本地/服务器检查脚本
├── tests/                 # 最小自动化测试
├── deploy.sh              # SSH 部署脚本
├── DEPLOYMENT.md          # 部署与回滚说明
└── .env.example           # 环境变量示例
```

## 本地运行

```bash
python app.py
```

默认访问：

```text
http://127.0.0.1:8000/predict
```

Windows 上也可以继续使用：

```text
启动预测系统.bat
```

## 环境变量

如需覆盖默认配置，复制一份 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

常用配置：

```text
HOST=127.0.0.1
PORT=8000
BASE_PATH=/predict
STATIC_DIR=static
DB_PATH=data/changsha_prediction.db
LOG_DIR=logs
LOG_LEVEL=INFO
```

## 检查与测试

```bash
python scripts/check.py
```

这个命令会做两件事：

- 检查主要 Python 文件语法
- 运行 `tests/` 下的单元测试

## 部署

长期维护推荐使用：

```text
Git commit -> Git push -> SSH 登录服务器 -> git pull -> bash deploy.sh --apply
```

完整流程见 [DEPLOYMENT.md](DEPLOYMENT.md)。

## 日志

运行日志默认写入：

```text
logs/app.log
```

日志会自动轮转，避免单个日志文件无限增长。

## 维护原则

- 预测逻辑修改后，先运行 `python scripts/check.py`。
- 涉及服务器目录、服务重启、Nginx 配置修改时，先备份再操作。
- 不把 `dist/`、本地打包产物、虚拟环境、日志提交到 Git。
- 线上部署前确认服务器工作区没有未记录的手动改动。
