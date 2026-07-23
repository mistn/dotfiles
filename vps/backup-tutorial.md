# VPS 全自动打包备份教程

## 第一步：创建/更新脚本文件

```bash
nano /opt/backup.sh
```

清空或替换为以下全新代码：

```bash
#!/bin/bash

# =========================================
# VPS 全自动打包备份脚本
# =========================================

TEMP_DIR="/tmp/vps_backup"
DATE=$(date +%Y%m%d_%H%M%S)
FILE_NAME="vps_backup_${DATE}.tar.gz"

REMOTE_NAME="infini"             # 已配置好的 rclone 名称
REMOTE_DIR="vps_backup"          # 网盘上的全新保存文件夹（无需手动创建，自动生成）
RETENTION_DAYS=7                 # 云端自动保留最近 7 天的备份

# 1. 创建本地临时打包目录
mkdir -p $TEMP_DIR

# 2. 打包核心文件与数据 (Nginx 配置+证书、Wallos 数据、脚本自身)
tar -czf ${TEMP_DIR}/${FILE_NAME} \
    /etc/nginx \
    /opt/wallos \
    /opt/backup.sh 2>/dev/null

# 3. 直接上传压缩包至 WebDAV 云端新文件夹中
rclone copy ${TEMP_DIR}/${FILE_NAME} ${REMOTE_NAME}:${REMOTE_DIR}

# 4. 自动删除云端超过 7 天的旧备份
rclone delete --min-age ${RETENTION_DAYS}d ${REMOTE_NAME}:${REMOTE_DIR}

# 5. 清理 VPS 本地临时文件
rm -rf $TEMP_DIR

echo "[$(date +'%Y-%m-%d %H:%M:%S')] 备份完成！压缩包已成功同步至 ${REMOTE_NAME}:${REMOTE_DIR}"
```

按 `Ctrl + O` 保存，按 `Enter` 确认，再按 `Ctrl + X` 退出。

## 第二步：赋予执行权限并测试运行

```bash
# 1. 赋予可执行权限
chmod +x /opt/backup.sh

# 2. 手动运行一次脚本
/opt/backup.sh
```

## 第三步：验证上传结果

```bash
# 查看文件夹列表，应该能看到新增了 vps_backup
rclone lsd infini:

# 查看新文件夹里面的备份文件
rclone ls infini:vps_backup
```

## 第四步：定时任务设置

确保每天凌晨 3:00 自动默默运行备份：

```bash
crontab -e
```

在文件最底端加入这一行（已有则无需重复）：

```
0 3 * * * /bin/bash /opt/backup.sh > /dev/null 2>&1
```

大功告成！
