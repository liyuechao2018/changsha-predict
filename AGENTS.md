# AI Agent 维护说明

这个项目用于预测长沙中考录取参考结果。维护时请把稳定性和可回滚性放在第一位。

## 开始前

1. 先阅读 `README.md` 和 `DEPLOYMENT.md`。
2. 先运行或建议运行 `python scripts/check.py`。
3. 先查看 Git 状态，不要覆盖用户未提交改动。
4. 不要把 `dist/`、日志、虚拟环境、打包产物提交到 Git。

## 修改边界

- 预测数据在 `database.py`。
- 预测算法在 `prediction_engine.py`。
- HTTP 服务和路由在 `app.py`。
- 环境变量和路径在 `config.py`。
- 前端文件在 `static/`。

如果只是部署或运维，不要改预测算法。

## 必须先确认的操作

以下操作必须先向用户确认：

- 删除文件或目录
- 覆盖服务器项目目录
- 修改 Nginx 配置
- 重启线上服务
- 执行 `deploy.sh --apply`
- 执行 `git reset --hard`
- 修改线上数据库文件

## 检查命令

```bash
python scripts/check.py
```

服务器健康检查：

```bash
curl -fsS http://127.0.0.1:8000/predict/api/health
```

公网检查：

```bash
curl -I https://www.liyuechao.com/predict
```

## 部署原则

优先使用 Git + SSH：

```bash
git pull --ff-only origin main
bash deploy.sh
bash deploy.sh --apply
```

`bash deploy.sh` 是演练模式。只有用户确认后，才执行 `bash deploy.sh --apply`。
