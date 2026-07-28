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
tar -zxvf /tmp/restore/vps_backup_*.tar.gz -C /
rm -rf /tmp/restore
```

解压后 `/etc/nginx`、`/opt/memos`、`/opt/wallos`、`/opt/openlist`、`/opt/manyacg`、`/opt/backup.sh` 全部归位。

## 4. 拉起服务

**OpenList**（官方脚本安装，先装依赖再覆盖数据）：

```bash
# 运行当初使用的官方一键安装脚本
systemctl stop openlist
systemctl daemon-reload
systemctl enable --now openlist
```

**Docker 容器**：

```bash
docker run -d --name memos --restart unless-stopped \
  -p 127.0.0.1:5230:5230 \
  -v /opt/memos:/var/opt/memos \
  neosmemo/memos:stable
```

Wallos、ManyACG 用原本的 `docker run` 或 `docker-compose` 命令拉起。

**Nginx**：

```bash
nginx -t && systemctl start nginx
```

## 5. DNS + 定时备份

Cloudflare 将所有 A 记录 IP 改到新 VPS。

安装 acme.sh 并设置定时备份：

```bash
curl https://get.acme.sh | sh

crontab -e
```

末尾添加：

```
0 3 * * * /bin/bash /opt/backup.sh > /dev/null 2>&1
```
