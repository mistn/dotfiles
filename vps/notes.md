# VPS 运维备忘

## Vaultwarden 修改主邮箱

无需配置 SMTP，启动容器时加两行环境变量即可：

```
LOG_LEVEL=debug
EXTENDED_LOGGING=true
```
