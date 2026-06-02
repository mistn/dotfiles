local mp = require("mp")

-- ================= 配置区 ================= --
local KEY = "SPACE"                   -- 绑定的按键 (推荐 "SPACE" 或 "RIGHT")
local SPEED_FAST = 3.0                -- 长按触发的倍速
local HOLD_DELAY = 0.3                -- 按下多久后视为长按（单位：秒）
local SHORT_PRESS_CMD = "cycle pause" -- 短按时执行的命令 
-- 提示：
-- 如果你把 KEY 改成 "RIGHT" (右方向键)
-- 建议把 SHORT_PRESS_CMD 改成 "seek 5" (快进5秒)
-- ========================================== --

local original_speed = 1.0
local timer = nil
local is_holding = false
local is_down = false

function start_speedup()
    if is_down and not is_holding then
        is_holding = true
        original_speed = mp.get_property_native("speed")
        mp.set_property_native("speed", SPEED_FAST)
        mp.osd_message("⏩ 长按倍速: " .. SPEED_FAST .. "x", 1)
    end
end

function on_key(table)
    if table.event == "down" then
        is_down = true
        is_holding = false
        if timer then timer:kill() end
        -- 启动定时器：达到判定时间后触发倍速
        timer = mp.add_timeout(HOLD_DELAY, start_speedup)
        
    elseif table.event == "up" then
        is_down = false
        if timer then
            timer:kill()
            timer = nil
        end
        
        if is_holding then
            -- 如果已经触发了长按倍速，松手时恢复原来的速度
            is_holding = false
            mp.set_property_native("speed", original_speed)
            mp.osd_message("▶ 恢复速度: " .. original_speed .. "x", 1)
        else
            -- 如果没达到长按时间就被松开，判定为短按，执行原本的命令
            mp.command(SHORT_PRESS_CMD)
        end
    end
end

-- {complex = true} 允许 mpv 捕获按下 (down) 和松开 (up) 动作
mp.add_key_binding(KEY, "smart_hold_speedup", on_key, {complex = true})