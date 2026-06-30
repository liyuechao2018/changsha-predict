# 宝塔部署说明

## 1. 上传目录

建议上传并解压到：

```text
/www/wwwroot/changsha-predict
```

## 2. 宝塔 Python 项目

在宝塔面板安装并打开「Python项目管理器」，新建项目：

```text
项目名称：changsha-predict
项目路径：/www/wwwroot/changsha-predict
Python版本：Python 3.9+ 即可
启动文件：app.py
启动命令：bash start.sh
端口：8000
```

当前项目无第三方依赖，`requirements.txt` 可以留空安装。

## 3. Nginx 反向代理

如果你的域名是：

```text
predict.example.com
```

在宝塔「网站」里添加站点，然后配置反向代理：

```text
目标URL：http://127.0.0.1:8000
```

访问链路：

```text
https://predict.example.com
↓
Nginx
↓
http://127.0.0.1:8000
```

## 4. SSL

在宝塔网站设置中申请 Let's Encrypt SSL，并开启强制 HTTPS。

## 5. 数据库权限

确保运行用户可以读写：

```text
/www/wwwroot/changsha-predict/data
```

SQLite 数据库文件：

```text
data/changsha_prediction.db
```

## 6. 重要声明

页面已包含免责声明：

```text
预测结果仅供志愿填报参考，不构成录取承诺；实际录取以长沙市教育局最终公布为准。
```

## 7. 常见问题

如果网站打不开：

1. 检查 Python 项目是否运行。
2. 检查 8000 端口是否被占用。
3. 检查反向代理目标是否为 `http://127.0.0.1:8000`。
4. 查看项目日志是否有报错。
