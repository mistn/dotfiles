# dotfiles

个人配置备份，换电脑快速复原。

## mpv

视频播放器，基于 [mpv](https://mpv.io) + [uosc](https://github.com/tomasklaen/uosc) 打造。

![](images/mpv.png)

- `mpv.conf` — 主配置文件（快捷键、解码、画质等）
- `script-opts/uosc.conf` — uosc 界面配置
- `scripts/` — 脚本（uosc 控件、长按倍速等）
- `fonts/` — uosc 图标字体

## Rime

中文输入法，基于 [雾凇拼音](https://github.com/iDvel/rime-ice)。

![](images/rime.png)

- `default.custom.yaml` — 全局自定义
- `weasel.custom.yaml` — 小狼毫前端配置
- `rime_ice.custom.yaml` — 雾凇拼音补丁
- `double_pinyin_flypy.custom.yaml` — 双拼方案补丁
- `custom_phrase.txt` — 自定义短语
- 其余为雾凇拼音上游词库、方案、Lua 脚本

## fastfetch

终端信息展示工具，基于 [fastfetch](https://github.com/fastfetch-cli/fastfetch)。

- `config.jsonc` — 主配置（模块布局、颜色主题等）
- `ascii.txt` — ASCII 艺术字

## Windows Terminal

终端应用，基于 [Windows Terminal](https://github.com/microsoft/terminal)。

- `settings.json` — 配色、字体、按键绑定等

## 使用

```powershell
# 克隆
git clone https://github.com/mistn/dotfiles.git

# mpv — 将 portable_config 软链接到 scoop mpv 目录
New-Item -ItemType SymbolicLink -Path "$env:SCOOP\persist\mpv\portable_config" -Target "D:\dotfiles\mpv\portable_config"

# Rime — 将 Rime 目录软链接到 Rime 用户目录
New-Item -ItemType SymbolicLink -Path "$env:APPDATA\Rime" -Target "D:\dotfiles\Rime"

# fastfetch — 将 fastfetch 目录软链接到 .config
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.config\fastfetch" -Target "D:\dotfiles\fastfetch"

# Windows Terminal — 将 settings.json 软链接到 Terminal 配置目录
$WT = Resolve-Path "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_*\LocalState"
New-Item -ItemType SymbolicLink -Path "$WT\settings.json" -Target "D:\dotfiles\terminal\settings.json"
```
