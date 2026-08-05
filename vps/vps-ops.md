# VPS 运维手册（整合版）

> 适用环境：Debian 13 / Nginx + Docker / acme.sh / Cloudflare
> 整合自：部署新服务 SOP、全量迁移 SOP、自动备份教程、域名更换实战记录

## 目录

1. [当前服务清单](#1-当前服务清单)
2. [部署新服务 SOP](#2-部署新服务-sop)
3. [添加 / 更换域名指南](#3-添加--更换域名指南)
4. [全量迁移 SOP](#4-全量迁移-sop)
5. [自动备份教程](#5-自动备份教程)

---

## 1. 当前服务清单

| 服务 | 容器名 | 内网端口 | 域名 | 数据目录 |
|------|--------|----------|------|----------|
| Wallos（账单） | `wallos` | `127.0.0.1:8282` | `wallos.[主域名]` | `/opt/wallos` |
| OpenList（网盘） | `list` | `127.0.0.1:5244` | `list.[主域名]` | `/opt/list` |
| ManyACG（漫画） | `manyacg` | — | — | `/opt/manyacg` |

公共信息：
- VPS 公网 IP：`[你的VPS公网IP]`
- Nginx SSL 监听端口：`4443`（配合 Cloudflare 443 源站端口）
- 证书目录：`/etc/nginx/cert/`
- 主域名：`[主域名]`（旧域名 `[旧域名]` 已弃用）

---

## 2. 部署新服务 SOP

### 2.1 Docker 部署

```bash
mkdir -p /opt/[软件名]

# 提示：若镜像存在权限问题（如 OpenList），可在命令中加 --user 0:0
docker run -d \
  --name [软件名] \
  --restart unless-stopped \
  -p 127.0.0.1:[新端口]:[容器内部端口] \
  -v /opt/[软件名]:[容器内数据路径] \
  [镜像名称]:[标签]
```

### 2.2 DNS + 证书

```bash
# Cloudflare 添加 A 记录 → 灰色云朵（避免 522），等待生效

# 申请证书（临时停 Nginx 释放 80 端口）
systemctl stop nginx
~/.acme.sh/acme.sh --issue -d [二级域名].[主域名] --standalone --listen-v4

# 安装证书
~/.acme.sh/acme.sh --install-cert -d [二级域名].[主域名] \
  --key-file       /etc/nginx/cert/[二级域名].[主域名].key \
  --fullchain-file /etc/nginx/cert/[二级域名].[主域名].crt
```

> 推荐直接使用第 3 章的 DNS API 方式申请，可免去停 nginx、且自动续签更可靠。

### 2.3 Nginx 配置

```bash
nano /etc/nginx/conf.d/[二级域名].[主域名].conf
```

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name [二级域名].[主域名];
    return 301 https://$host$request_uri;
}

server {
    listen 4443 ssl;
    listen [::]:4443 ssl;
    http2 on;
    server_name [二级域名].[主域名];

    ssl_certificate /etc/nginx/cert/[二级域名].[主域名].crt;
    ssl_certificate_key /etc/nginx/cert/[二级域名].[主域名].key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Cloudflare 真实 IP
    set_real_ip_from 127.0.0.1;
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 104.16.0.0/13;
    set_real_ip_from 104.24.0.0/14;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 131.0.72.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 162.158.0.0/15;
    set_real_ip_from 172.64.0.0/13;
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    real_ip_header CF-Connecting-IP;

    location / {
        proxy_pass http://127.0.0.1:[新端口];
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 0;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2.4 启动并回 Cloudflare 点亮橙色云朵

```bash
nginx -t && systemctl start nginx
```

浏览器访问 `https://[二级域名].[主域名]:4443` 验证。

### 2.5 纳入自动备份

```bash
nano /opt/backup.sh
```

在 `tar` 命令追加 `/opt/[软件名]`，更新 `echo` 提示信息，手动运行 `/opt/backup.sh` 验证。

---

## 3. 添加 / 更换域名指南

> 以下为本次 `[旧域名] → [主域名]` 换域名实战记录（wallos + list），已归纳成通用步骤。
> 核心原则：**proxy_pass 端口永远不变**，只改 `server_name` 与证书路径。

### 3.1 查看现状（改前必看）

```bash
ls /etc/nginx/conf.d/
grep -rnE "server_name|proxy_pass" /etc/nginx/conf.d/ | grep -iE "wallos|list"
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

### 3.2 Cloudflare DNS

添加 A 记录（先**灰色云朵**，测试通过再点亮）：

| 类型 | 名称 | 内容 | 代理状态 |
|------|------|------|---------|
| A | `wallos` | VPS IP | 灰色云朵 |
| A | `list` | VPS IP | 灰色云朵 |

验证解析：

```bash
dig +short wallos.[主域名]
dig +short list.[主域名]
```

### 3.3 申请并安装证书（推荐 DNS API 方式，无需停 nginx）

> 若用 standalone 方式：先 `systemctl stop nginx` 释放 80 端口，签完再启动。

配置 Cloudflare Token（只需一次）：

```bash
export CF_Token="你的Cloudflare_Token"
echo "CF_Token='你的Cloudflare_Token'" >> /root/.acme.sh/account.conf
```

申请 + 安装（`--force` 用于已有证书时强制切换方式）：

```bash
~/.acme.sh/acme.sh --force --issue -d wallos.[主域名] --dns dns_cf
~/.acme.sh/acme.sh --force --issue -d list.[主域名] --dns dns_cf

~/.acme.sh/acme.sh --install-cert -d wallos.[主域名] \
  --key-file /etc/nginx/cert/wallos.[主域名].key \
  --fullchain-file /etc/nginx/cert/wallos.[主域名].crt \
  --reloadcmd "systemctl reload nginx"

~/.acme.sh/acme.sh --install-cert -d list.[主域名] \
  --key-file /etc/nginx/cert/list.[主域名].key \
  --fullchain-file /etc/nginx/cert/list.[主域名].crt \
  --reloadcmd "systemctl reload nginx"
```

> `--reloadcmd` 让续签成功后自动重载 nginx，不用手动操作。

### 3.4 复制旧配置改成新域名（端口别动）

```bash
# 整体把 [旧域名] 替换成 [主域名]，其余字段（尤其 proxy_pass）保持不变
sed 's/[旧域名]/[主域名]/g' /etc/nginx/conf.d/wallos.[旧域名].conf > /etc/nginx/conf.d/wallos.[主域名].conf
sed 's/[旧域名]/[主域名]/g' /etc/nginx/conf.d/list.[旧域名].conf > /etc/nginx/conf.d/list.[主域名].conf

# 核对关键行
grep -nE "server_name|ssl_certificate|proxy_pass" /etc/nginx/conf.d/wallos.[主域名].conf
grep -nE "server_name|ssl_certificate|proxy_pass" /etc/nginx/conf.d/list.[主域名].conf
```

预期：`proxy_pass` 保持 `8282` / `5244` 不变，证书指向新域名。

### 3.5 测试并启动

```bash
nginx -t && systemctl start nginx
```

### 3.6 应用内域名（关键，别漏）

- **Wallos**：网页后台 → Settings → **URL** 改为 `https://wallos.[主域名]`
- **OpenList**：配置里的站点 / 分享链接域名改为 `https://list.[主域名]`

### 3.7 收尾

```bash
# 确认正式证书（issuer 应为 R3/E1/YE1/YE2 等，而非 Fake LE / STG）
echo | openssl s_client -connect 127.0.0.1:4443 -servername wallos.[主域名] 2>/dev/null | openssl x509 -noout -issuer -subject -dates

# 删旧 conf 并重载
rm /etc/nginx/conf.d/wallos.[旧域名].conf /etc/nginx/conf.d/list.[旧域名].conf
nginx -t && systemctl reload nginx
```

Cloudflare：两条记录点亮橙色云朵，SSL/TLS 模式设为 Full 或 Full strict。

### 3.8 续签注意点（重要）

- 证书是 **standalone** 模式申请的会有坑：nginx 占着 80 端口，自动续签时 acme.sh 无法监听 → **续签失败，证书静默过期**。
- 解决办法：换成 **Cloudflare DNS API（`--dns dns_cf`）**，不走 80 端口，续签最稳。
- 验证续签配置：

```bash
grep Le_Webroot /root/.acme.sh/wallos.[主域名]_ecc/wallos.[主域名].conf   # 应为 dns_cf
grep Le_Webroot /root/.acme.sh/list.[主域名]_ecc/list.[主域名].conf
grep CF_Token /root/.acme.sh/account.conf | sed 's/\(CF_Token="\).*/\1***/'   # 确认 Token 已持久化
```

- 旧的 `[旧域名]` / `[旧域名]` 证书可清理：

```bash
~/.acme.sh/acme.sh --remove -d wallos.[旧域名]
~/.acme.sh/acme.sh --remove -d list.[旧域名]
~/.acme.sh/acme.sh --remove -d wallos.[旧域名]
~/.acme.sh/acme.sh --remove -d list.[旧域名]
```

---

## 4. 全量迁移 SOP

### 4.1 初始化环境

```bash
apt update && apt install nginx curl rclone -y
curl -fsSL https://get.docker.com | bash
systemctl enable docker --now
```

### 4.2 拉取备份

```bash
rclone config  # 配置名称保持 infini
mkdir -p /tmp/restore
rclone copy infini:vps_backup/ /tmp/restore/
```

### 4.3 解压恢复

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

### 4.4 拉起服务

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
#    Wallos 参考：-p 127.0.0.1:8282:80  -v /opt/wallos:...

# 3. 启动 Nginx 反向代理
nginx -t && systemctl start nginx
```

### 4.5 DNS + 证书与定时任务

Cloudflare 解析：将所有域名 A 记录的 IP 修改为新 VPS 的 IP。

安装 acme.sh（用于自动续签证书）：

```bash
curl https://get.acme.sh | sh
```

> 迁移后注意：证书按第 3 章流程重新签发（或恢复旧证书并确保续签方式为 dns_cf）。

恢复定时备份任务：

```bash
crontab -e
```

在末尾添加一行：

```
0 3 * * * /bin/bash /opt/backup.sh > /dev/null 2>&1
```

---

## 5. 自动备份教程

### 5.1 创建/更新脚本文件

```bash
nano /opt/backup.sh
```

```bash
#!/bin/bash
# =========================================
# VPS 全自动打包备份脚本
# =========================================

TEMP_DIR="/tmp/vps_backup"
DATE=$(date +%Y%m%d_%H%M%S)
FILE_NAME="vps_backup_${DATE}.tar.gz"

REMOTE_NAME="infini"             # rclone 配置的网盘名称
REMOTE_DIR="vps_backup"          # 云端存储文件夹
RETENTION_DAYS=7                 # 云端保留最近 7 天的备份

# 1. 创建本地临时打包目录
mkdir -p $TEMP_DIR

# 2. 打包核心文件与数据（已排除缓存与日志，节省空间）
#    - /etc/nginx      : Nginx 站点配置 + 所有 SSL 证书
#    - /opt/wallos     : Wallos 账单数据库 + 数据
#    - /opt/list       : OpenList 网盘数据库 + 配置文件 (原 /opt/openlist)
#    - /opt/manyacg    : ManyACG 数据库 + 配置文件 + data
#    - /opt/backup.sh  : 备份脚本自身
tar -czf ${TEMP_DIR}/${FILE_NAME} \
    --exclude='*manyacg/imgcache*' \
    --exclude='*manyacg/logs*' \
    /etc/nginx \
    /opt/wallos \
    /opt/list \
    /opt/manyacg \
    /opt/backup.sh 2>/dev/null

# 3. 直接上传压缩包至 WebDAV 云端文件夹
rclone copy ${TEMP_DIR}/${FILE_NAME} ${REMOTE_NAME}:${REMOTE_DIR}

# 4. 自动清理云端超过 7 天的旧备份
rclone delete --min-age ${RETENTION_DAYS}d ${REMOTE_NAME}:${REMOTE_DIR}

# 5. 清理 VPS 本地临时打包文件
rm -rf $TEMP_DIR

echo "[$(date +'%Y-%m-%d %H:%M:%S')] 备份完成！已包含 Nginx配置/证书、Wallos、OpenList(/opt/list) 及 ManyACG。"
```

按 `Ctrl + O` 保存，`Enter` 确认，`Ctrl + X` 退出。

### 5.2 赋予执行权限并测试运行

```bash
chmod +x /opt/backup.sh
/opt/backup.sh
```

### 5.3 验证上传结果

```bash
rclone lsd infini:
rclone ls infini:vps_backup
```

### 5.4 定时任务设置

```bash
crontab -e
```

在文件最底端加入一行（已有则无需重复）：

```bash
0 3 * * * /bin/bash /opt/backup.sh > /dev/null 2>&1
```

> 注意：备份脚本无需随域名更换改动——`/etc/nginx`（含新 conf 与证书）本就在打包范围内；acme.sh 续签后的证书自动重装到 `/etc/nginx/cert`，同样被覆盖。

---

## 附录：本次换域名时间线（2026-08-05）

1. 确认目标：wallos、list 由 `[旧域名]` 迁移至 `[主域名]`
2. Cloudflare 添加两条 A 记录（灰云）→ 解析到 VPS 公网 IP
3. standalone 方式签发两张证书并装入 `/etc/nginx/cert/`
4. `sed` 复制旧 conf 生成新 conf，仅替换域名，端口（8282/5244）不变
5. `nginx -t` 通过，本地 `curl -H "Host:..."` 验证两个域名反代正常
6. 发现 standalone 续签会被 80 端口卡死 → 改用 Cloudflare DNS API（dns_cf）
7. 创建 Cloudflare Token → `--force --issue --dns dns_cf` 重签 → `--install-cert` 加 `--reloadcmd`
8. 手动把 `CF_Token` 写入 `~/.acme.sh/account.conf`（acme.sh 未自动持久化）
9. `--renew --force --test` 验证续签链路，确认正式证书（issuer YE2）生效
10. 待办：删旧 conf、应用内 URL（Wallos/OpenList）、确认橙云、清理旧证书
