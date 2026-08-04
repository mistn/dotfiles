# VPS 全量迁移 SOP

## 1. 初始化环境

```bash
apt update && apt install nginx curl rclone -y
curl -fsSL https://get.docker.com | bash
systemctl enable docker --now
```

## 2. 拉取备份

```bash
rclone config  # 配置名称保持 infini
mkdir -p /tmp/restore
rclone copy infini:vps_backup/ /tmp/restore/
```

## 3. 解压恢复

```bash
# 找到最新备份并解压归位
tar -zxvf /tmp/restore/vps_backup_*.tar.gz -C /
rm -rf /tmp/restore
```

解压完成后，以下路径已自动归位：

- `/etc/nginx` — Nginx 配置与所有 SSL 证书
- `/opt/list` — OpenList 网盘数据与配置
- `/opt/wallos` — Wallos 账单数据
- `/opt/manyacg` — ManyACG 数据库与数据
- `/opt/backup.sh` — 自动备份脚本自身

## 4. 拉起服务

```bash
# 1. 拉起 OpenList 容器
docker run -d \
  --name list \
  --restart unless-stopped \
  --user 0:0 \
  -p 127.0.0.1:5244:5244 \
  -v /opt/list:/opt/openlist/data \
  -e UMASK=022 \
  openlistteam/openlist:latest

# 2. 拉起 Wallos、ManyACG 等其他容器（使用各自原本的 docker run 或 docker-compose 命令）

# 3. 启动 Nginx 反向代理
nginx -t && systemctl start nginx
```

## 5. DNS + 证书与定时任务

Cloudflare 解析：将所有域名 A 记录的 IP 修改为新 VPS 的 IP。

安装 acme.sh（用于自动续签证书）：

```bash
curl https://get.acme.sh | sh
```

恢复定时备份任务：

```bash
crontab -e
```

在末尾添加一行：

```
0 3 * * * /bin/bash /opt/backup.sh > /dev/null 2>&1
```
