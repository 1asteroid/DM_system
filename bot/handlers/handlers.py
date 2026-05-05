from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.services.api_client import api_client
from bot.keyboards.keyboards import (
    main_menu, topics_keyboard, topic_actions,
    conversations_keyboard, risk_keyboard, contacts_action_keyboard,
)

router = Router()

STATUS_LABEL = {
    'draft': '⚪ Qoralama', 'pending': '🟡 Kutmoqda',
    'approved': '🟢 Tasdiqlangan', 'rejected': '🔴 Rad etilgan',
}


# ── FSM ──────────────────────────────────────────

class LoginStates(StatesGroup):
    email    = State()
    password = State()


class MessageStates(StatesGroup):
    selecting_contact = State()
    composing         = State()


# ── START ─────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    user = await api_client.get_me(msg.from_user.id)
    if user:
        await api_client.save_telegram_id(msg.from_user.id)
        await msg.answer(
            f"👋 Xush kelibsiz, *{user['full_name']}*!\n\nRol: `{user['role']}`",
            parse_mode="Markdown",
            reply_markup=main_menu(user['role'])
        )
    else:
        await msg.answer(
            "🎓 *Diplom Monitoring Tizimi*\n\nKirish uchun emailingizni yuboring:",
            parse_mode="Markdown"
        )
        await state.set_state(LoginStates.email)


# ── LOGIN ─────────────────────────────────────────

@router.message(LoginStates.email)
async def get_email(msg: Message, state: FSMContext):
    await state.update_data(email=msg.text)
    await msg.answer("🔑 Parolingizni kiriting:")
    await state.set_state(LoginStates.password)


@router.message(LoginStates.password)
async def get_password(msg: Message, state: FSMContext):
    data = await state.get_data()
    result = await api_client.login(data['email'], msg.text)
    await state.clear()

    if result:
        api_client.save_tokens(msg.from_user.id, result)
        await api_client.save_telegram_id(msg.from_user.id)
        user = result['user']
        await msg.answer(
            f"✅ Muvaffaqiyatli kirdingiz!\n\n👤 *{user['full_name']}*\nRol: `{user['role']}`",
            parse_mode="Markdown",
            reply_markup=main_menu(user['role'])
        )
    else:
        await msg.answer("❌ Email yoki parol noto'g'ri. Qayta urinib ko'ring: /start")


# ── DASHBOARD ─────────────────────────────────────

@router.message(F.text == "📊 Dashboard")
async def show_dashboard(msg: Message):
    stats = await api_client.dashboard(msg.from_user.id)
    if not stats:
        return await msg.answer("❌ Ma'lumot yuklashda xatolik. Avval /start orqali kiring.")

    text = (
        f"📊 *Dashboard*\n\n"
        f"📚 Jami mavzular: *{stats['total_topics']}*\n"
        f"🟢 Tasdiqlangan: *{stats['approved']}*\n"
        f"🟡 Kutmoqda: *{stats['pending']}*\n"
        f"🔴 Rad etilgan: *{stats['rejected']}*\n"
        f"⚪ Qoralama: *{stats['draft']}*\n\n"
        f"📈 O'rtacha progress: *{stats['avg_progress']}%*"
    )
    await msg.answer(text, parse_mode="Markdown")


# ── MAVZULAR ──────────────────────────────────────

STAGE_STATUS_ICON = {
    'not_started': '⬜',
    'in_progress': '🔄',
    'submitted':   '📤',
    'approved':    '✅',
    'rejected':    '❌',
}
STAGE_STATUS_LABEL = {
    'not_started': 'Boshlanmagan',
    'in_progress': 'Jarayonda',
    'submitted':   'Yuborilgan',
    'approved':    'Tasdiqlangan',
    'rejected':    'Rad etilgan',
}


@router.message(F.text == "📚 Mavzularim")
async def show_topics(msg: Message):
    topics = await api_client.get_topics(msg.from_user.id)
    if not topics:
        return await msg.answer("📭 Hozircha mavzular yo'q.")

    await msg.answer(
        "📚 *Mavzularingiz:*\n\nBatafsil ko'rish uchun tanlang 👇",
        parse_mode="Markdown",
        reply_markup=topics_keyboard(topics)
    )


@router.message(F.text == "📚 Barcha mavzular")
async def show_all_topics(msg: Message):
    topics = await api_client.get_topics(msg.from_user.id)
    if not topics:
        return await msg.answer("📭 Hozircha mavzular yo'q.")

    await msg.answer(
        "📚 *Barcha mavzular:*\n\nBatafsil ko'rish uchun tanlang 👇",
        parse_mode="Markdown",
        reply_markup=topics_keyboard(topics)
    )


@router.message(F.text == "👨‍🎓 Talabalarim")
async def show_my_students(msg: Message):
    topics = await api_client.get_topics(msg.from_user.id)
    if not topics:
        return await msg.answer("📭 Hozircha talabalar yo'q.")

    await msg.answer(
        "👨‍🎓 *Talabalarim:*\n\nBatafsil ko'rish uchun tanlang 👇",
        parse_mode="Markdown",
        reply_markup=topics_keyboard(topics)
    )


@router.message(F.text == "📋 Vazifalar")
async def show_supervisor_tasks(msg: Message):
    topics = await api_client.get_topics(msg.from_user.id)
    if not topics:
        return await msg.answer("📭 Hozircha vazifalar yo'q.")

    pending = [t for t in topics if t.get('status') == 'pending']
    text = "📋 *Tasdiqlash kutayotgan mavzular:*\n\n"
    if not pending:
        text = "📋 *Vazifalar*\n\n✅ Barcha mavzular ko'rib chiqilgan."
    else:
        for t in pending:
            student_name = t.get('student_name') or 'Noma\'lum'
            text += f"🟡 *{t['title'][:40]}*\n👤 {student_name}\n\n"

    await msg.answer(text, parse_mode="Markdown")


@router.message(F.text == "👥 Foydalanuvchilar")
async def show_users_admin(msg: Message):
    await msg.answer(
        "👥 *Foydalanuvchilar*\n\nFoydalanuvchini qidirish uchun:\n/search <ism yoki email>",
        parse_mode="Markdown"
    )


@router.message(F.text == "📈 Hisobotlar")
async def show_reports(msg: Message):
    stats = await api_client.dashboard(msg.from_user.id)
    if not stats:
        return await msg.answer("❌ Ma'lumot yuklashda xatolik.")

    text = (
        f"📈 *Tizim Hisoboti*\n\n"
        f"📚 Jami mavzular: *{stats['total_topics']}*\n"
        f"🟢 Tasdiqlangan: *{stats['approved']}*\n"
        f"🟡 Kutmoqda: *{stats['pending']}*\n"
        f"🔴 Rad etilgan: *{stats['rejected']}*\n"
        f"⚪ Qoralama: *{stats['draft']}*\n\n"
        f"📈 O'rtacha progress: *{stats['avg_progress']}%*"
    )
    await msg.answer(text, parse_mode="Markdown")


@router.callback_query(F.data.startswith("topic:"))
async def topic_detail(call: CallbackQuery):
    topic_id = int(call.data.split(":")[1])
    topic = await api_client.get_topic(call.from_user.id, topic_id)
    if not topic:
        return await call.answer("Mavzu topilmadi", show_alert=True)

    status = topic.get('status', '')
    status_line = STATUS_LABEL.get(status, status)

    text = f"📄 *{topic['title']}*\n\n"
    text += f"📌 Holat: {status_line}\n"
    text += f"📈 Progress: *{topic['progress']}%*\n"
    text += f"📅 O'quv yili: {topic['academic_year']}\n"

    if status == 'approved' and topic.get('approved_at'):
        text += f"✅ Tasdiqlangan: {topic['approved_at'][:10]}\n"
    elif status == 'rejected':
        reason = topic.get('reject_reason') or '—'
        text += f"❌ *Rad etish sababi:* _{reason}_\n"

    if topic.get('description'):
        text += f"\n📝 _{topic['description'][:200]}_\n"

    stages = topic.get('stages') or []
    if stages:
        approved_count = sum(1 for s in stages if s.get('status') == 'approved')
        text += f"\n📋 *Bosqichlar* ({approved_count}/{len(stages)} tasdiqlangan):\n"
        for s in stages:
            icon = STAGE_STATUS_ICON.get(s.get('status', ''), '⬜')
            label = STAGE_STATUS_LABEL.get(s.get('status', ''), s.get('status', ''))
            deadline = f"  ⏰ {s['deadline'][:10]}" if s.get('deadline') else ''
            text += f"{icon} *{s['name']}* — _{label}_{deadline}\n"
            if s.get('status') == 'rejected' and s.get('comment'):
                text += f"   💬 _{s['comment'][:80]}_\n"
    else:
        text += "\n📋 *Bosqichlar:* _Hali qo'shilmagan_\n"

    await call.message.edit_text(text, parse_mode="Markdown",
                                  reply_markup=topic_actions(topic_id, status))
    await call.answer()


# ── BILDIRISHNOMALAR ──────────────────────────────

@router.message(F.text == "🔔 Bildirishnomalar")
async def show_notifications(msg: Message):
    notifs = await api_client.get_notifications(msg.from_user.id)
    if not notifs:
        return await msg.answer("🔔 Yangi bildirishnomalar yo'q.")

    unread = [n for n in notifs if not n['is_read']]
    text = f"🔔 *Bildirishnomalar* ({len(unread)} o'qilmagan)\n\n"

    TYPE_ICON = {
        'status_changed': '🔄',
        'new_task': '📋',
        'meeting_scheduled': '📅',
        'deadline_reminder': '⏰',
        'file_uploaded': '📎',
        'comment_added': '💬',
    }

    for n in notifs[:15]:
        icon = "🔵" if not n['is_read'] else "⚪"
        type_icon = TYPE_ICON.get(n.get('type', ''), '📌')
        text += f"{icon} {type_icon} *{n['title']}*\n{n.get('body', '')}\n\n"

    await msg.answer(text, parse_mode="Markdown")


# ── XABARLAR ──────────────────────────────────────

@router.message(F.text == "💬 Xabarlar")
async def show_conversations(msg: Message):
    contacts = await api_client.get_contacts(msg.from_user.id)
    if not contacts:
        return await msg.answer(
            "💬 Hozircha yozishmalar yo'q.\n\nYangi suhbat boshlash uchun foydalanuvchi qidiring: /search",
            parse_mode="Markdown"
        )

    total_unread = sum(c['unread_count'] for c in contacts)
    text = f"💬 *Yozishmalar*"
    if total_unread:
        text += f" ({total_unread} o'qilmagan)"
    text += "\n\nSuhbatdoshingizni tanlang:"
    await msg.answer(text, parse_mode="Markdown", reply_markup=conversations_keyboard(contacts))


@router.callback_query(F.data.startswith("conv:"))
async def show_conversation(call: CallbackQuery):
    parts = call.data.split(":", 2)
    other_user_id = int(parts[1])
    partner_name = parts[2] if len(parts) > 2 else "Foydalanuvchi"

    messages_list = await api_client.get_conversation(call.from_user.id, other_user_id)
    me = await api_client.get_me(call.from_user.id)
    my_id = me['id'] if me else None

    header = f"💬 *{partner_name}* bilan yozishmalar\n\n"
    body_parts = []

    if messages_list:
        for m in messages_list[-20:]:
            ts = m['created_at'][:16].replace('T', ' ')
            if m['sender_id'] == my_id:
                body_parts.append(f"➡️ *Siz* ({ts}):\n{m['content']}\n\n")
            else:
                body_parts.append(f"⬅️ *{partner_name}* ({ts}):\n{m['content']}\n\n")
    else:
        body_parts.append("_(Xabarlar yo'q)_\n\n")

    body = "".join(body_parts)
    max_body = 4000 - len(header)
    if max_body > 10 and len(body) > max_body:
        body = "…\n\n" + body[-(max_body - 4):]

    await call.message.edit_text(
        header + body,
        parse_mode="Markdown",
        reply_markup=contacts_action_keyboard(other_user_id, partner_name)
    )
    await call.answer()


@router.callback_query(F.data.startswith("reply:"))
async def start_reply(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":", 2)
    other_user_id = int(parts[1])
    partner_name = parts[2] if len(parts) > 2 else "Foydalanuvchi"

    await state.set_state(MessageStates.composing)
    await state.update_data(receiver_id=other_user_id, partner_name=partner_name)
    await call.message.answer(
        f"✏️ *{partner_name}*ga xabar yozing:\n_(Bekor qilish uchun /cancel)_",
        parse_mode="Markdown"
    )
    await call.answer()


@router.message(Command("cancel"))
async def cancel_state(msg: Message, state: FSMContext):
    await state.clear()
    user = await api_client.get_me(msg.from_user.id)
    role = user['role'] if user else 'student'
    await msg.answer("❌ Bekor qilindi.", reply_markup=main_menu(role))


@router.message(MessageStates.composing)
async def send_composed_message(msg: Message, state: FSMContext):
    data = await state.get_data()
    receiver_id = data.get('receiver_id')
    group_topic_id = data.get('group_topic_id')
    partner_name = data.get('partner_name', 'Foydalanuvchi')
    await state.clear()

    if group_topic_id:
        result = await api_client.send_group_message(msg.from_user.id, group_topic_id, msg.text)
        if result:
            await msg.answer("✅ Guruhga xabar yuborildi!")
        else:
            await msg.answer("❌ Xabar yuborilmadi.")
    elif receiver_id:
        result = await api_client.send_message(msg.from_user.id, receiver_id, msg.text)
        if result:
            await msg.answer(f"✅ Xabar *{partner_name}*ga yuborildi!", parse_mode="Markdown")
        else:
            await msg.answer("❌ Xabar yuborilmadi. Keyinroq urinib ko'ring.")
    else:
        await msg.answer("❌ Xatolik. Qaytadan urinib ko'ring.")


# ── USER SEARCH ────────────────────────────────────

@router.message(Command("search"))
async def search_users_cmd(msg: Message, state: FSMContext):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2 or len(args[1].strip()) < 2:
        return await msg.answer("🔍 Foydalanish: /search <ism yoki email>\nMisol: /search Alisher")

    query = args[1].strip()
    results = await api_client.search_users(msg.from_user.id, query)
    if not results:
        return await msg.answer(f"🔍 '{query}' bo'yicha hech kim topilmadi.")

    text = f"🔍 *'{query}' bo'yicha natijalar:*\n\n"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for u in results[:10]:
        role_icon = {'student': '🎓', 'supervisor': '👨‍🏫', 'admin': '👑', 'kafedra_head': '🏛️'}.get(u.get('role', ''), '👤')
        text += f"{role_icon} *{u['full_name']}* — `{u['email']}`\n"
        buttons.append([InlineKeyboardButton(
            text=f"💬 {u['full_name'][:30]}",
            callback_data=f"conv:{u['id']}:{u['full_name'][:20]}"
        )])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer(text, parse_mode="Markdown", reply_markup=kb)


# ── RAHBAR KONTAKTI ────────────────────────────────

@router.message(F.text == "👨‍🏫 Rahbarim")
async def show_my_supervisor(msg: Message):
    sup = await api_client.get_my_supervisor(msg.from_user.id)
    if not sup:
        return await msg.answer(
            "👨‍🏫 Hozircha ilmiy rahbar tayinlanmagan.\n\nRahbar tayinlangandan so'ng bu yerda uning kontakt ma'lumotlari ko'rinadi.",
            parse_mode="Markdown"
        )

    text = (
        f"👨‍🏫 *Ilmiy Rahbarim*\n\n"
        f"👤 Ism: *{sup['full_name']}*\n"
    )
    if sup.get('email'):
        text += f"📧 Email: `{sup['email']}`\n"
    if sup.get('phone'):
        text += f"📱 Telefon: `{sup['phone']}`\n"
    text += f"\n📚 Mavzu: _{sup.get('topic_title', '—')}_"

    await msg.answer(text, parse_mode="Markdown")


# ── GURUH SUHBAT ───────────────────────────────────

@router.message(F.text == "👥 Guruh suhbat")
async def show_group_chats(msg: Message):
    topics = await api_client.get_topics(msg.from_user.id)
    if not topics:
        return await msg.answer("📭 Guruh suhbat uchun mavzular yo'q.")

    text = "👥 *Guruh suhbatlar*\n\nMavzuni tanlang:"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [
        [InlineKeyboardButton(
            text=f"📚 {t['title'][:40]}",
            callback_data=f"group:{t['id']}"
        )]
        for t in topics[:10]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer(text, parse_mode="Markdown", reply_markup=kb)


@router.callback_query(F.data.startswith("group:"))
async def show_group_messages(call: CallbackQuery):
    topic_id = int(call.data.split(":")[1])
    msgs = await api_client.get_group_messages(call.from_user.id, topic_id)
    me = await api_client.get_me(call.from_user.id)
    my_id = me['id'] if me else None

    text = "👥 *Guruh suhbat*\n\n"
    if not msgs:
        text += "_(Xabarlar yo'q)_\n\nYangi xabar yuborish uchun /gmsg <mavzu_id> <xabar>"
    else:
        for m in msgs[-20:]:
            ts = m['created_at'][:16].replace('T', ' ')
            mark = "➡️ *Siz*" if m['sender_id'] == my_id else f"⬅️ *Foydalanuvchi #{m['sender_id']}*"
            text += f"{mark} ({ts}):\n{m['content']}\n\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✏️ Xabar yozish", callback_data=f"gmsg_compose:{topic_id}")
    ]])
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("gmsg_compose:"))
async def group_compose(call: CallbackQuery, state: FSMContext):
    topic_id = int(call.data.split(":")[1])
    await state.set_state(MessageStates.composing)
    await state.update_data(group_topic_id=topic_id)
    await call.message.answer(
        "✏️ Guruhga xabar yozing:\n_(Bekor qilish uchun /cancel)_",
        parse_mode="Markdown"
    )
    await call.answer()


@router.message(Command("gmsg"))
async def send_group_msg_cmd(msg: Message):
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        return await msg.answer("Foydalanish: /gmsg <mavzu_id> <xabar>\nMisol: /gmsg 5 Salom hammaga!")
    try:
        topic_id = int(parts[1])
    except ValueError:
        return await msg.answer("Mavzu ID raqam bo'lishi kerak.")
    content = parts[2]
    result = await api_client.send_group_message(msg.from_user.id, topic_id, content)
    if result:
        await msg.answer("✅ Guruhga xabar yuborildi!")
    else:
        await msg.answer("❌ Xabar yuborilmadi.")


# ── RISK MONITOR ──────────────────────────────

RISK_ICON = {'low': '🟢', 'medium': '🟡', 'high': '🔴', 'critical': '🚨'}
RISK_LABEL = {'low': 'Past', 'medium': "O'rta", 'high': 'Yuqori', 'critical': 'Kritik'}


@router.message(F.text == "⚠️ Risk Monitor")
async def show_risk_monitor(msg: Message):
    risks = await api_client.get_risk_assessments(msg.from_user.id)
    if not risks:
        topics = await api_client.get_topics(msg.from_user.id)
        if not topics:
            return await msg.answer("⚠️ Risk baholash uchun mavzular yo'q.")
        for t in topics[:5]:
            await api_client.assess_risk(msg.from_user.id, t['id'])
        risks = await api_client.get_risk_assessments(msg.from_user.id)
        if not risks:
            return await msg.answer("⚠️ Risk ma'lumotlari yuklanmadi.")

    critical = [r for r in risks if r['risk_level'] == 'critical']
    high     = [r for r in risks if r['risk_level'] == 'high']
    medium   = [r for r in risks if r['risk_level'] == 'medium']
    low      = [r for r in risks if r['risk_level'] == 'low']

    text = (
        f"⚠️ *Risk Monitori*\n\n"
        f"🚨 Kritik: *{len(critical)}*\n"
        f"🔴 Yuqori: *{len(high)}*\n"
        f"🟡 O'rta: *{len(medium)}*\n"
        f"🟢 Past: *{len(low)}*\n\n"
        f"Mavzuni tanlang:"
    )
    await msg.answer(text, parse_mode="Markdown", reply_markup=risk_keyboard(risks))


@router.callback_query(F.data.startswith("risk:"))
async def show_risk_detail(call: CallbackQuery):
    topic_id = int(call.data.split(":")[1])
    result = await api_client.assess_risk(call.from_user.id, topic_id)
    if not result:
        return await call.answer("Risk baholashda xatolik", show_alert=True)

    import json
    try:
        factors = json.loads(result.get('factors', '[]'))
    except json.JSONDecodeError:
        factors = []

    icon = RISK_ICON.get(result['risk_level'], '⚪')
    label = RISK_LABEL.get(result['risk_level'], result['risk_level'])

    text = (
        f"{icon} *Risk Baholash*\n\n"
        f"Daraja: *{label}*\n"
        f"Ball: *{result['risk_score']:.0f}/100*\n\n"
    )
    if factors:
        text += "*Omillar:*\n"
        SEV_ICON = {'critical': '🚨', 'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        for f in factors:
            text += f"{SEV_ICON.get(f.get('severity', 'low'), '•')} {f.get('message', '')}\n"
    if result.get('recommendation'):
        text += f"\n💡 *Tavsiya:*\n{result['recommendation']}"

    await call.message.edit_text(text, parse_mode="Markdown")
    await call.answer()


# ── PROFIL ────────────────────────────────────────

@router.message(F.text == "👤 Profil")
async def show_profile(msg: Message):
    user = await api_client.get_me(msg.from_user.id)
    if not user:
        return await msg.answer("❌ Avval /start orqali kiring.")

    text = (
        f"👤 *Profilingiz*\n\n"
        f"Ism: *{user['full_name']}*\n"
        f"Email: `{user['email']}`\n"
        f"Rol: `{user['role']}`\n"
        f"Holat: {'✅ Faol' if user['is_active'] else '❌ Faol emas'}"
    )
    if user.get('phone'):
        text += f"\nTelefon: `{user['phone']}`"
    await msg.answer(text, parse_mode="Markdown")
