from aqt import mw
from aqt.qt import QAction, QPushButton, qconnect, QTimer
from aqt.utils import showInfo

from .gist_updater import get_anki_data, update_gist

def sync_to_gist():
    try:
        data = get_anki_data()
        update_gist(data)
        showInfo(f"✅ 同步成功！\n今日学习: {data['today_learned']} 张\n时长: {data['duration_minutes']} 分钟")
    except Exception as e:
        showInfo(f"❌ 同步失败:\n{str(e)}")

def add_sync_button():
    button = QPushButton("同步")
    button.setFixedSize(64, 24)
    button.setStyleSheet("""
        QPushButton {
            background-color: #111111;
            color: #ffffff;
            border: none;
            font-size: 12px;
            border-radius: 4px;
            font-weight: 500;
            padding: 0 12px;
        }
        QPushButton:hover {
            background-color: #333333;
        }
        QPushButton:pressed {
            background-color: #000000;
        }
    """)
    qconnect(button.clicked, sync_to_gist)
    
    toolbar = mw.addToolBar("Gist")
    toolbar.setMovable(False)
    toolbar.addWidget(button)

# 保留菜单
action = QAction("🔄 同步到 Gist", mw)
qconnect(action.triggered, sync_to_gist)
mw.form.menuTools.addAction(action)

# 延迟添加按钮
QTimer.singleShot(500, add_sync_button)