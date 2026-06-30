# SSH 标准部署说明

本文档用于把长沙中考录取预测系统从“宝塔网页手动部署”整理为“Git + SSH + 命令行部署”流程。

## 1. 当前项目判断

### 技术栈

- 后端：Python 标准库 `http.server`
- 数据库：SQLite，文件位于 `data/changsha_prediction.db`
- 前端：原生 HTML / CSS / JavaScript
- 构建：无前端构建步骤，无打包步骤
- 依赖：当前 `requirements.txt` 没有实际第三方依赖
- 默认监听：`HOST=127.0.0.1`，`PORT=8000`
- 访问前缀：`/predict`
- 配置入口：`.env` 或系统环境变量，示例见 `.env.example`
- 日志目录：`logs/app.log`

### 启动方式

本地或服务器直接启动：

```bash
bash start.sh
```

等价于：

```bash
HOST=127.0.0.1 PORT=8000 python3 app.py
```

生产环境推荐通过 `.env` 管理配置：

```bash
cp .env.example .env
```

常用环境变量：

```text
HOST=127.0.0.1
PORT=8000
BASE_PATH=/predict
STATIC_DIR=static
DB_PATH=data/changsha_prediction.db
LOG_DIR=logs
LOG_LEVEL=INFO
```

健康检查：

```bash
curl -fsS http://127.0.0.1:8000/predict/api/health
```

正常返回应类似：

```json
{"ok": true}
```

## 2. 服务器当前已知信息

根据此前宝塔页面和部署过程，当前推断如下：

- 服务器 IP：`175.178.216.16`
- 线上域名：`www.liyuechao.com`
- 访问路径：`https://www.liyuechao.com/predict`
- 项目目录：`/www/wwwroot/changsha-predict`
- 应用端口：`8000`
- 进程管理：目前可能由宝塔 Python 项目管理器管理
- Nginx：应存在将 `/predict` 转发到 `http://127.0.0.1:8000` 的配置

仍需 SSH 确认的信息：

- 服务器项目目录是否已经是 Git 仓库
- 当前进程到底由 `systemd`、`supervisor`、宝塔 Python 项目管理器，还是手动进程管理
- Nginx 站点配置文件路径
- 是否已有明确服务名，例如 `changsha-predict`、`predict` 等

## 3. 首次 SSH 检查命令

登录服务器：

```bash
ssh root@175.178.216.16
```

进入项目目录：

```bash
cd /www/wwwroot/changsha-predict
```

检查项目文件：

```bash
pwd
ls -la
ls -la static data
ls -la logs
```

检查 Git 状态：

```bash
git status
git rev-parse --short HEAD
```

如果提示 `not a git repository`，说明服务器目录还没有接入 Git。

检查端口：

```bash
ss -lntp | grep ':8000'
```

检查进程：

```bash
ps aux | grep -E 'python|app.py|changsha|predict' | grep -v grep
```

运行项目自检：

```bash
python3 scripts/check.py
```

检查 Nginx 配置：

```bash
nginx -T | grep -n -A20 -B10 'liyuechao.com'
nginx -T | grep -n -A20 -B10 'predict'
```

这些命令只读取状态，不会修改服务器。

## 4. Git 标准部署流程

### 本地开发流程

确认本地项目是 Git 仓库：

```bash
git status
```

如果当前项目还不是 Git 仓库，首次需要执行：

```bash
git init
git add app.py database.py prediction_engine.py static start.sh requirements.txt README.md DEPLOYMENT.md deploy.sh
git commit -m "Initial deployable version"
git branch -M main
git remote add origin <你的Git仓库地址>
git push -u origin main
```

以后每次修改代码：

```bash
git status
git add .
git commit -m "描述本次修改"
python scripts/check.py
git push
```

建议不要把这些内容提交到 Git：

- `__pycache__/`
- `dist/`
- `launcher/bin/`
- `launcher/obj/`
- 本地打包产物
- 服务器日志

### 服务器首次接入 Git

在确认线上目录已经备份后，再选择一种方式。

方式 A：保留旧目录，重新 clone：

```bash
cd /www/wwwroot
mv changsha-predict changsha-predict.bak.$(date +%Y%m%d_%H%M%S)
git clone <你的Git仓库地址> changsha-predict
cd changsha-predict
```

方式 B：在旧目录中初始化 Git：

```bash
cd /www/wwwroot/changsha-predict
git init
git remote add origin <你的Git仓库地址>
git fetch origin main
git status
```

方式 B 更容易遇到本地文件冲突，推荐先用方式 A。

## 5. 最小可用部署流程

本地：

```bash
git add .
git commit -m "Update predictor"
git push
```

服务器：

```bash
ssh root@175.178.216.16
cd /www/wwwroot/changsha-predict
git status
git pull --ff-only origin main
python3 -m py_compile app.py database.py prediction_engine.py
```

现在推荐改用：

```bash
python3 scripts/check.py
```

安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

当前项目没有实际第三方依赖，所以这一步通常不会安装任何东西。

重启服务需要先确认服务管理方式。确认前不要随意执行重启命令。

如果是 systemd：

```bash
systemctl restart changsha-predict
systemctl status changsha-predict --no-pager
```

如果是 supervisor：

```bash
supervisorctl status
supervisorctl restart changsha-predict
```

如果仍由宝塔 Python 项目管理器管理，需要先通过 SSH 查清它实际生成的 supervisor/systemd 配置，再固化为命令。

最后检查：

```bash
curl -fsS http://127.0.0.1:8000/predict/api/health
curl -I https://www.liyuechao.com/predict
```

## 6. deploy.sh 使用方式

本仓库提供了 `deploy.sh`，用于在服务器项目目录中执行标准部署。

默认是演练模式，不会真正修改文件：

```bash
cd /www/wwwroot/changsha-predict
bash deploy.sh
```

确认项目目录、Git 仓库、服务名或重启命令都正确后，再执行：

```bash
cd /www/wwwroot/changsha-predict
bash deploy.sh --apply
```

常用参数：

```bash
PROJECT_DIR=/www/wwwroot/changsha-predict \
BRANCH=main \
HEALTH_URL=http://127.0.0.1:8000/predict/api/health \
bash deploy.sh
```

如果已经确认 systemd 服务名：

```bash
SERVICE_NAME=changsha-predict bash deploy.sh --apply
```

如果已经确认重启命令：

```bash
RESTART_CMD='supervisorctl restart changsha-predict' bash deploy.sh --apply
```

`deploy.sh --apply` 会做这些事：

1. 检查项目目录和 `app.py`
2. 记录当前 Git 状态
3. 备份当前目录到 `/www/backup/changsha-predict/`
4. `git fetch` 和 `git pull --ff-only`
5. 如有依赖则安装依赖
6. 执行 `scripts/check.py` 做基础检查
7. 按配置重启服务
8. 执行健康检查

## 7. Nginx 参考配置

如果站点是 `www.liyuechao.com`，并希望挂在 `/predict` 下，Nginx 反向代理可参考：

```nginx
location /predict/ {
    proxy_pass http://127.0.0.1:8000/predict/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location = /predict {
    proxy_pass http://127.0.0.1:8000/predict;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

修改 Nginx 前必须先备份配置：

```bash
nginx -T > /root/nginx.before.predict.$(date +%Y%m%d_%H%M%S).conf
```

修改后检查：

```bash
nginx -t
```

确认无误后再重载：

```bash
systemctl reload nginx
```

## 8. 回滚方式

### Git 回滚

查看历史：

```bash
git log --oneline -5
```

回到上一个版本：

```bash
git reset --hard HEAD~1
```

然后重启服务。

注意：`git reset --hard` 会丢弃未提交改动，执行前必须确认。

### 备份包回滚

`deploy.sh --apply` 会在部署前备份项目目录。

查看备份：

```bash
ls -lh /www/backup/changsha-predict
```

恢复备份示例：

```bash
cd /www/wwwroot
mv changsha-predict changsha-predict.failed.$(date +%Y%m%d_%H%M%S)
mkdir changsha-predict
tar -xzf /www/backup/changsha-predict/<备份文件>.tar.gz -C changsha-predict
```

恢复后重启服务并检查健康接口。

## 9. 常见故障

### 页面能打开但没有样式

通常是静态资源路径不对。确认 `static/index.html` 中是：

```html
<link rel="stylesheet" href="/predict/static/styles.css" />
<script src="/predict/static/app.js"></script>
```

### 点击预测没有反应

检查 JavaScript 是否加载：

```bash
curl -I https://www.liyuechao.com/predict/static/app.js
```

应返回 `200`。

### 502 Bad Gateway

通常是 Python 服务没启动或端口不对：

```bash
ss -lntp | grep ':8000'
curl -fsS http://127.0.0.1:8000/predict/api/health
```

### 查看运行日志

```bash
tail -n 100 /www/wwwroot/changsha-predict/logs/app.log
```

### 部署脚本只演练不执行

这是正常设计。直接运行：

```bash
bash deploy.sh
```

只会显示将要执行的命令。确认服务名和路径后，再运行：

```bash
bash deploy.sh --apply
```

### 404 Not Found

检查 Nginx 是否把 `/predict` 转发到了 Python 服务，或者应用是否支持 `/predict` 前缀。

### 数据无法写入

检查数据库目录权限：

```bash
ls -la /www/wwwroot/changsha-predict/data
```

运行用户需要能读写 `data/changsha_prediction.db`。

## 10. 下一步建议

建议先完成三件事：

1. 把本地项目正式放进 Git 仓库。
2. 通过 SSH 确认服务器项目目录、服务管理方式和 Nginx 配置。
3. 把宝塔 Python 项目管理器替换或固化为明确的 `systemd` 服务。
