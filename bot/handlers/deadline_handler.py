from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.services.api_client import api_client
from bot.keyboards.keyboards import deadline_keyboard

router = Router()


DEADLINE_WARNING_DAYS = 3


@router.message(Command("deadlines"))
@router.message(F.text == "⏰ Deadlinelar")
async def show_deadlines(msg: Message):
    """Shows upcoming deadlines"""
    topics = await api_client.get_topics(msg.from_user.id)
    if not topics:
        return await msg.answer("⏰ Hozircha deadlinelar yo'q.")

    from datetime import datetime, timedelta
    now = datetime.now()
    warning_date = now + timedelta(days=DEADLINE_WARNING_DAYS)

    upcoming = []
    for t in topics:
        stages = t.get('stages') or []
        for s in stages:
            deadline_str = s.get('deadline')
            if not deadline_str:
                continue
            try:
                deadline_dt = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                local_deadline = deadline_dt.replace(tzinfo=None)
                if local_deadline >= now:
                    days_left = (local_deadline - now).days
                    if days_left <= DEADLINE_WARNING_DAYS and s.get('status') != 'approved':
                        upcoming.append({
                            'topic_title': t.get('title', ''),
                            'stage_name': s.get('name', ''),
                            'deadline': deadline_str,
                            'days_left': days_left,
                            'status': s.get('status', ''),
                        })
            except Exception:
                continue
        if t.get('defense_date'):
            defense_str = t.get('defense_date')
            try:
                defense_dt = datetime.fromisoformat(defense_str.replace('Z', '+00:00'))
                local_defense = defense_dt.replace(tzinfo=None)
                if local_defense >= now:
                    days_left = (local_defense - now).days
                    if days_left <= DEADLINE_WARNING_DAYS:
                        upcoming.append({
                            'topic_title': t.get('title', ''),
                            'stage_name': '🎓 Mudofaa',
                            'deadline': defense_str,
                            'days_left': days_left,
                            'status': 'defense',
                        })
            except (ValueError, TypeError):
                pass

    if not upcoming:
        return await msg.answer(
            f"⏰ {DEADLINE_WARNING_DAYS} kun ichida deadlinelar yo'q.",
            reply_markup=deadline_keyboard()
        )

    upcoming.sort(key=lambda x: x['days_left'])

    text = f"⏰ *Yaqinlashayotgan deadlinelar*\n({DEADLINE_WARNING_DAYS} kun ichida)\n\n"
    for item in upcoming[:10]:
        days = item['days_left']
        if days <= 0:
            icon = "🚨"
            days_text = "Bugun!"
        elif days == 1:
            icon = "⚠️"
            days_text = "1 kun qoldi"
        else:
            icon = "⏰"
            days_text = f"{days} kun qoldi"

        status_icon = "✅" if item['status'] == 'approved' else "📤"
        text += f"{icon} *{days_text}*\n"
        text += f"  📚 {item['topic_title'][:40]}\n"
        text += f"  📋 {item['stage_name']}\n\n"

    await msg.answer(text, parse_mode="Markdown", reply_markup=deadline_keyboard())


@router.callback_query(F.data == "refresh_deadlines")
async def refresh_deadlines(call: CallbackQuery):
    """Refresh deadlines list"""
    await call.message.delete()
    await show_deadlines(call.message)
    await call.answer()


@router.callback_query(F.data == "my_deadlines")
async def my_deadlines_callback(call: CallbackQuery):
    """Show only my deadlines"""
    topics = await api_client.get_topics(call.from_user.id)
    if not topics:
        await call.answer("Mavzular yo'q", show_alert=True)
        return

    from datetime import datetime, timedelta
    now = datetime.now()

    my_deadlines = []
    for t in topics:
        stages = t.get('stages') or []
        for s in stages:
            deadline_str = s.get('deadline')
            if not deadline_str:
                continue
            try:
                deadline_dt = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                local_deadline = deadline_dt.replace(tzinfo=None)
                if local_deadline >= now:
                    days_left = (local_deadline - now).days
                    if days_left <= DEADLINE_WARNING_DAYS and s.get('status') != 'approved':
                        my_deadlines.append({
                            'topic_title': t.get('title', ''),
                            'stage_name': s.get('name', ''),
                            'days_left': days_left,
                            'status': s.get('status', ''),
                        })
            except (ValueError, TypeError):
                pass

    if not my_deadlines:
        await call.answer(f"{DEADLINE_WARNING_DAYS} kun ichida sizning deadlinelaringiz yo'q", show_alert=True)
        return

    my_deadlines.sort(key=lambda x: x['days_left'])

    text = f"⏰ *Sizning deadlinelaringiz*\n\n"
    for item in my_deadlines:
        days = item['days_left']
        if days <= 0:
            icon = "🚨"
            days_text = "Bugun!"
        elif days == 1:
            icon = "⚠️"
            days_text = "1 kun qoldi"
        else:
            icon = "⏰"
            days_text = f"{days} kun qoldi"

        text += f"{icon} *{days_text}*\n"
        text += f"  📚 {item['topic_title'][:40]}\n"
        text += f"  📋 {item['stage_name']}\n\n"

    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=deadline_keyboard())
    await call.answer()