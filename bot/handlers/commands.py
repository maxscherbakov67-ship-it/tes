from aiogram import Router, F, Bot
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from bot.texts import (
welcome_msg,
settings_msg,
help_msg,
start_conversation_msg,
)
from bot.keyboards import (
main_menu_keyboard,
settings_keyboard,
start_conversation_keyboard,
goback_keyboard,
set_prompt_keyboard,
create_prompt_keyboard,
choose_llm_keyboard,
choose_mode_keyboard,
new_conversation_keyboard,
previous_conversations_keyboard,
ChatCB,
PromptCB,
chats_kb,
prompts_kb
)
from bot.states import Botstate as bst
from bot.states import PromptForm
from database import storage

router = Router()

@router.callback_query(F.data == "noop")
async def noop(call: CallbackQuery):
    await call.answer()


    # ---------- Чаты ----------

async def render_chats(user_id: int, page: int = 0):
    total = await storage.count_chats(user_id)
    page = storage.clamp_page(page, total)
    pages = storage.total_pages(total)
    chats = await storage.get_chats_page(user_id, page)
    active_id = await storage.get_active_id(user_id)

    text = f"Ваши диалоги ({total}):" if total else "Диалогов пока нет. Создайте первый."
    return text, chats_kb(chats, active_id, page, pages)


@router.message(Command("chats"))
async def cmd_chats(message: Message):
    text, kb = await render_chats(message.from_user.id)
    await message.answer(text, reply_markup=kb)


@router.callback_query(ChatCB.filter())
async def on_chat(call: CallbackQuery, callback_data: ChatCB):
    user_id = call.from_user.id
    page = callback_data.page

    if callback_data.action == "new":
        await storage.create_chat(user_id)
        page = 0                                   # новый чат первый в списке
    elif callback_data.action == "delete":
        await storage.delete_chat(user_id, callback_data.id)
    elif callback_data.action == "open":
        await storage.set_active(user_id, callback_data.id)
    # action == "page": данные не меняем, только перерисуем

    text, kb = await render_chats(user_id, page)
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        pass                                       # "message is not modified"
    await call.answer()


# ---------- Промпты ----------

async def render_prompts(user_id: int, page: int = 0):
    total = await storage.count_custom_prompts(user_id)
    page = storage.clamp_page(page, total)
    pages = storage.total_pages(total)
    customs = await storage.get_custom_prompts_page(user_id, page)
    return "Выберите роль для текущего диалога:", prompts_kb(customs, page, pages)


@router.message(Command("prompts"))
async def cmd_prompts(message: Message):
    text, kb = await render_prompts(message.from_user.id)
    await message.answer(text, reply_markup=kb)


@router.callback_query(PromptCB.filter())
async def on_prompt(call: CallbackQuery, callback_data: PromptCB, state: FSMContext):
    user_id = call.from_user.id
    action = callback_data.action

    if action == "new":
        await state.set_state(PromptForm.waiting_text)
        await call.message.answer("Отправьте текст промпта:")
        return await call.answer()

    if action in ("preset", "custom"):
        chat_id = await storage.get_active_id(user_id)
        if chat_id is None:
            return await call.answer("Сначала создайте диалог: /chats", show_alert=True)

        if action == "preset":
            title, text = storage.PRESET_PROMPTS[callback_data.id]
        else:
            row = await storage.get_custom_prompt(user_id, callback_data.id)
            if row is None:
                return await call.answer("Промпт не найден", show_alert=True)
            title, text = row["title"], row["text"]

        await storage.set_system_prompt(chat_id, text)
        return await call.answer(f"Роль «{title}» установлена")

    if action == "delete":
        await storage.delete_custom_prompt(user_id, callback_data.id)

    # delete / page: перерисовываем список
    text, kb = await render_prompts(user_id, callback_data.page)
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        pass
    await call.answer()


@router.message(PromptForm.waiting_text, F.text)
async def save_prompt(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    title = text[:20] + ("…" if len(text) > 20 else "")

    await storage.add_custom_prompt(user_id, title, text)
    await state.clear()

    chat_id = await storage.get_active_id(user_id)
    if chat_id:
        await storage.set_system_prompt(chat_id, text)   # сразу применяем

    await message.answer("Промпт сохранён и применён. Все свои промпты: /prompts")

#СТАРТ
@router.message(Command("start"))
async def cmd_start(message, state: FSMContext):
    await state.set_state(bst.start)
    await message.answer(welcome_msg, reply_markup=main_menu_keyboard())
#ХЕЛП
@router.message(Command("help"))
async def cmd_help(message, state: FSMContext):
    await state.set_state(bst.help)
    await message.answer(help_msg, reply_markup=goback_keyboard())


#НАСТРОЙКИ
@router.callback_query(bst.start, F.data == "settings")
async def cmd_settings(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data
    await state.set_state(bst.settings)
    await callback.message.edit_text(settings_msg, reply_markup=settings_keyboard())
    await callback.answer()
#ПОСТАВИТЬ/ВЫБРАТЬ ПРОМПТ
@router.callback_query(bst.settings, F.data == "set_prompt")
async def cmd_set_prompt(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data
    await state.set_state(bst.set_prompt)
    await callback.message.edit_text(set_prompt_msg, reply_markup=set_prompt_keyboard())
    await callback.answer()
#СОЗДАТЬ ПРОМПТ
@router.callback_query(bst.set_prompt)
async def cmd_create_prompt(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data
    await state.set_state(bst.create_prompt)
    await callback.message.edit_text(create_prompt_msg, reply_markup=create_prompt_keyboard())
    await callback.answer()
#ВЫБРАТЬ ЛЛМ/МОДЕЛЬ
@router.callback_query(bst.settings, F.data == "choose_llm")
async def cmd_choose_llm(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data
    await state.set_state(bst.choose_llm)
    await callback.message.edit_text(choose_llm_msg, reply_markup=choose_llm_keyboard())
    await callback.answer()


#МЕНЮ ДИАЛОГОВ/ЧАТОВ 
@router.callback_query(bst.start, F.data == "start_conversation")
async def cmd_start_conversation(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data
    await state.set_state(bst.conversation_menu)
    await callback.message.edit_text(start_conversation_msg, reply_markup=start_conversation_keyboard())
    await callback.answer()
#ВЫБОР РЕЖИМА
@router.callback_query(bst.conversation_menu)
async def cmd_choose_mode(callback: CallbackQuery, state:FSMContext):
    callback_data = callback.data
    await state.set_state(bst.choose_mode)
    await callback.message.edit_text(choose_mode_msg, reply_markup=choose_mode_keyboard())
    await callback.answer()
#НОВЫЙ ДИАЛОГ/ЧАТ
@router.callback_query(bst.conversation_menu)
async def cmd_new_conversation(callback: CallbackQuery, state:FSMContext):
    callback_data = callback.data
    await state.set_state(bst.new_conversation)
    await callback.message.edit_text(new_conversation_msg, reply_markup=new_conversation_keyboard())
    await callback.answer()
#ПРЕДЫДУЩИЕ ДИАЛОГИ/ЧАТЫ
@router.callback_query(bst.conversation_menu)
async def cmd_previous_conversations(callback: CallbackQuery, state:FSMContext):
    callback_data = callback.data
    await state.set_state(bst.previous_conversations)
    await callback.message.edit_text(previous_conversations_msg, reply_markup=previous_conversations_keyboard())
    await callback.answer()
