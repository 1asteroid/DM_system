from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu(role: str) -> ReplyKeyboardMarkup:
    if role == 'student':
        keyboard = [
            [KeyboardButton(text="📚 Mavzularim"), KeyboardButton(text="👨‍🏫 Rahbarim")],
            [KeyboardButton(text="⏰ Deadlinelar"), KeyboardButton(text="🔔 Bildirishnomalar")],
            [KeyboardButton(text="👤 Profil")],
        ]
    elif role == 'supervisor':
        keyboard = [
            [KeyboardButton(text="👨‍🎓 Talabalarim"), KeyboardButton(text="📋 Vazifalar")],
            [KeyboardButton(text="⏰ Deadlinelar"), KeyboardButton(text="🔔 Bildirishnomalar")],
            [KeyboardButton(text="👤 Profil")],
        ]
    elif role in ('admin', 'kafedra_head'):
        keyboard = [
            [KeyboardButton(text="📊 Dashboard"), KeyboardButton(text="👥 Foydalanuvchilar")],
            [KeyboardButton(text="📚 Barcha mavzular"), KeyboardButton(text="⚠️ Risk Monitor")],
            [KeyboardButton(text="🔔 Bildirishnomalar"), KeyboardButton(text="📈 Hisobotlar")],
            [KeyboardButton(text="👤 Profil")],
        ]
    else:
        keyboard = [
            [KeyboardButton(text="🔔 Bildirishnomalar"), KeyboardButton(text="👤 Profil")],
        ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


_TOPIC_STATUS_ICON = {
    'draft':    '⚪',
    'pending':  '🟡',
    'approved': '🟢',
    'rejected': '🔴',
}


def topics_keyboard(topics: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{_TOPIC_STATUS_ICON.get(t.get('status', ''), '📄')} {t['title'][:38]}",
            callback_data=f"topic:{t['id']}"
        )]
        for t in topics
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def topic_actions(topic_id: int, status: str) -> InlineKeyboardMarkup:
    btns = [[InlineKeyboardButton(text="📋 Bosqichlar", callback_data=f"stages:{topic_id}")]]
    if status == 'draft':
        btns.append([InlineKeyboardButton(text="📤 Tasdiqlashga yuborish", callback_data=f"submit:{topic_id}")])
    return InlineKeyboardMarkup(inline_keyboard=btns)


def conversations_keyboard(contacts: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"💬 {c['full_name']}" + (f" 🔵{c['unread_count']}" if c['unread_count'] else ""),
            callback_data=f"conv:{c['user_id']}:{c['full_name'][:20]}"
        )]
        for c in contacts
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def contacts_action_keyboard(user_id: int, name: str) -> InlineKeyboardMarkup:
    """Inline keyboard shown after viewing a conversation — allows replying."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✏️ Javob yozish", callback_data=f"reply:{user_id}:{name[:20]}"),
    ]])


def risk_keyboard(risks: list) -> InlineKeyboardMarkup:
    ICONS = {'low': '🟢', 'medium': '🟡', 'high': '🔴', 'critical': '🚨'}
    buttons = [
        [InlineKeyboardButton(
            text=f"{ICONS.get(r['risk_level'], '⚪')} {r['topic_title'][:35]} ({r['risk_score']:.0f})",
            callback_data=f"risk:{r['topic_id']}"
        )]
        for r in risks[:10]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def deadline_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for deadline menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_deadlines")],
        [InlineKeyboardButton(text="📋 Faqat mening deadlinelarim", callback_data="my_deadlines")],
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])
