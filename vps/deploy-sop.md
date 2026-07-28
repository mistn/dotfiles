# VPS 部署新服务 SOP

## 1. Docker 部署

```bash
mkdir -p /opt/[软件名]

docker run -d \
  --name [软件名] \
  --restart unless-stopped \
  -p 127.0.0.1:[新端口]:[容器内部端口] \
  -v /opt/[软件名]:[容器内数据路径] \
  [镜像名称]:[标签]
```

## 2. DNS + 证书

```bash
# Cloudflare 添加 A 记录 → 灰色云朵（避免 522），等待生效

# 申请证书（临时停 Nginx 释放 80 端口）
systemctl stop nginx
~/.acme.sh/acme.sh --issue -d [二级域名].miuo.me --standalone --listen-v4

# 安装证书
~/.acme.sh/acme.sh --install-cert -d [二级域名].miuo.me \
  --key-file       /etc/nginx/cert/[二级域名].miuo.me.key \
  --fullchain-file /etc/nginx/cert/[二级域名].miuo.me.crt
```

## 3. Nginx 配置

```bash
nano /etc/nginx/conf.d/[二级域名].miuo.me.conf
```

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name [二级域名].miuo.me;
    return 301 https://$host$request_uri;
}

server {
    listen 4443 ssl;
    listen [::]:4443 ssl;
    http2 on;
    server_name [二级域名].miuo.me;

    ssl_certificate /etc/nginx/cert/[二级域名].miuo.me.crt;
    ssl_certificate_key /etc/nginx/cert/[二级域名].miuo.me.key;

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

## 4. 启动并回 Cloudflare 点亮橙色云朵

```bash
nginx -t && systemctl start nginx
```

浏览器访问 `https://[二级域名].miuo.me` 验证。

## 5. 纳入自动备份

```bash
nano /opt/backup.sh
```

在 `tar` 命令追加 `/opt/[软件名]`，更新 `echo` 提示信息，手动运行 `/opt/backup.sh` 验证。
