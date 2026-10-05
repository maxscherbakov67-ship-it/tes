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
choose_llm_msg,
choose_mode_msg,
new_conversation_msg,
previous_conversations_msg,
set_prompt_msg,
create_prompt_msg
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
ModelCB,
chats_kb,
prompts_kb,
chat_manage_kb,
prompt_manage_kb,
prompt_view_kb,
models_kb
)
from bot.states import Botstate as bst
from bot.states import PromptForm, RenameForm
from database import storage
from services import llm_storage

BACK_ROUTES = {
    bst.help.state:                   (bst.start, welcome_msg, main_menu_keyboard),
    bst.settings.state:               (bst.start, welcome_msg, main_menu_keyboard),
    bst.conversation_menu.state:      (bst.start, welcome_msg, main_menu_keyboard),
    bst.set_prompt.state:             (bst.settings, settings_msg, settings_keyboard),
    bst.choose_llm.state:             (bst.settings, settings_msg, settings_keyboard),
    bst.choose_mode.state:            (bst.conversation_menu, start_conversation_msg, start_conversation_keyboard),
    bst.new_conversation.state:       (bst.conversation_menu, start_conversation_msg, start_conversation_keyboard),
    bst.previous_conversations.state: (bst.conversation_menu, start_conversation_msg, start_conversation_keyboard),
    RenameForm.waiting_title.state: (bst.conversation_menu, start_conversation_msg, start_conversation_keyboard),
    PromptForm.waiting_text : (bst.conversation_menu, start_conversation_msg, start_conversation_keyboard),

}

router = Router()

@router.callback_query(F.data == "noop")
async def noop(call: CallbackQuery):
    await call.answer()

async def render_models(user_id: int):
    models = await llm_storage.get_models()
    if not models:
        return "🤖 Моделей пока нет. Добавьте через add_model.py", None
    current = await llm_storage.get_user_model(user_id)
    return "🤖 Выберите модель:", models_kb(models, current["id"] if current else None)

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
async def on_chat(call: CallbackQuery, callback_data: ChatCB, state: FSMContext):
    user_id = call.from_user.id
    page = callback_data.page

    if callback_data.action == "rename":
        await state.update_data(rename_chat_id=callback_data.id, rename_page=page)
        await state.set_state(RenameForm.waiting_title)
        await call.message.answer("✏️ Пришли новое название чата:")
        return await call.answer()

    if callback_data.action == "new":
        await storage.create_chat(user_id)
        page = 0                                   # новый чат первый в списке
    elif callback_data.action == "delete":
        await storage.delete_chat(user_id, callback_data.id)
    elif callback_data.action == "open":
        await storage.set_active(user_id, callback_data.id)
    # action == "page": данные не меняем, только перерисуем
    if callback_data.action == "manage":
        chat = await storage.get_chat(user_id, callback_data.id)
        if chat is None:
            return await call.answer("Чат не найден", show_alert=True)
        await call.message.edit_text(
            f"⚙️ Чат «{chat['title']}»\nЧто сделать?",
            reply_markup=chat_manage_kb(chat, page),
        )
        return await call.answer()
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
        await call.message.answer("Отправьте текст промпта:", reply_markup=goback_keyboard())
        return await call.answer()

    if action == "view":  # посмотреть пресет
        title, text = storage.PRESET_PROMPTS[callback_data.id]
        await call.message.edit_text(f"📖 «{title}»\n\n{text}",
                                        reply_markup=prompt_view_kb(callback_data.id, callback_data.page))
        return await call.answer()

    if action == "manage":  # карточка своего промпта: видно, что внутри
        row = await storage.get_custom_prompt(user_id, callback_data.id)
        if row is None:
            return await call.answer("Промпт не найден", show_alert=True)
        await call.message.edit_text(f"⭐ «{row['title']}»\n\n{row['text']}",
                                     reply_markup=prompt_manage_kb(row, callback_data.page))
        return await call.answer()

    if action == "rename":
        await state.update_data(rename_prompt_id=callback_data.id, rename_page=callback_data.page)
        await state.set_state(PromptForm.rename_title)
        await call.message.answer("✏️ Пришли новое название промпта:")
        return await call.answer() 

    if action == "edit_text":
        await state.update_data(edit_prompt_id=callback_data.id, edit_page=callback_data.page)
        await state.set_state(PromptForm.edit_text)
        await call.message.answer("📝 Пришли новый текст промпта:")
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

    # запоминаем, с какого экрана пришли в форму
    data = await state.get_data()
    return_state = data.get("return_state")

    await storage.add_custom_prompt(user_id, title, text)
    chat_id = await storage.get_active_id(user_id)
    if chat_id:
        await storage.set_system_prompt(chat_id, text)

    await state.clear()
    if return_state:
        await state.set_state(return_state)   # возвращаем стейт экрана со списком

    msg, kb = await render_prompts(user_id)   # ← свежий список с клавиатурой
    await message.answer(f"✅ Промпт сохранён и применён.\n\n{msg}", reply_markup=kb)

@router.message(PromptForm.waiting_title, F.text)
async def save_prompt_title(message: Message, state: FSMContext):
    await state.update_data(prompt_title=message.text.strip()[:50])
    await state.set_state(PromptForm.waiting_text)
    await message.answer("Теперь отправь сам текст промпта:")

@router.message(PromptForm.waiting_text, F.text)
async def save_prompt_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    title = data.get("prompt_title") or "Без названия"
    text = message.text.strip()
    return_state = data.get("return_state")

    await storage.add_custom_prompt(user_id, title, text)
    chat_id = await storage.get_active_id(user_id)
    if chat_id:
        await storage.set_system_prompt(chat_id, text)

    await state.clear()
    if return_state:
        await state.set_state(return_state)

    msg, kb = await render_prompts(user_id)
    await message.answer(f"✅ Промпт «{title}» сохранён.\n\n{msg}", reply_markup=kb)


@router.message(PromptForm.rename_title, F.text)
async def apply_prompt_rename(message: Message, state: FSMContext):
    data = await state.get_data()
    prompt_id = data.get("rename_prompt_id")
    page = data.get("rename_page", 0)
    await state.clear()

    title = message.text.strip()[:50]
    if prompt_id is not None and title:
        await storage.rename_custom_prompt(message.from_user.id, prompt_id, title)

    msg, kb = await render_prompts(message.from_user.id, page)
    await message.answer(msg, reply_markup=kb)

@router.message(PromptForm.edit_text, F.text)
async def apply_prompt_text_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    prompt_id = data.get("edit_prompt_id")
    page = data.get("edit_page", 0)
    await state.clear()

    text = message.text.strip()
    if prompt_id is not None and text:
        await storage.update_custom_prompt_text(message.from_user.id, prompt_id, text)

    row = await storage.get_custom_prompt(message.from_user.id, prompt_id)
    if row is None:
        msg, kb = await render_prompts(message.from_user.id, page)
        return await message.answer(msg, reply_markup=kb)

    await message.answer(
        f"✅ Текст обновлён.\n\n⭐ «{row['title']}»\n\n{row['text']}",
        reply_markup=prompt_manage_kb(row, page),
    )
#MODELS
@router.callback_query(bst.settings, F.data == "choose_llm")
async def cmd_choose_llm(callback: CallbackQuery, state: FSMContext):
    await state.set_state(bst.choose_llm)
    text, kb = await render_models(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(ModelCB.filter())
async def on_model(call: CallbackQuery, callback_data: ModelCB):
    if callback_data.action == "pick":
        await llm_storage.set_user_model(call.from_user.id, callback_data.id)
        text, kb = await render_models(call.from_user.id)
        try:
            await call.message.edit_text(text, reply_markup=kb)
        except TelegramBadRequest:
            pass
        return await call.answer("Модель выбрана")
    await call.answer()

#СТАРТ
@router.message(Command("start"))
async def cmd_start(message, state: FSMContext):
    await state.set_state(bst.start)
    await message.answer(welcome_msg, reply_markup=main_menu_keyboard())
#ХЕЛП
@router.callback_query(bst.start, F.data == "help")
@router.message(Command("help"))
async def cmd_help(event: Message | CallbackQuery, state: FSMContext):
    await state.set_state(bst.help)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(help_msg, reply_markup=goback_keyboard())
        await event.answer()
    else:
        await event.answer(help_msg, reply_markup=goback_keyboard())


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
@router.callback_query(bst.set_prompt, F.data == "create_prompt")
async def cmd_create_prompt(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data
    await state.set_state(bst.create_prompt)
    await callback.message.edit_text(create_prompt_msg, reply_markup=create_prompt_keyboard())
    await callback.answer()


#МЕНЮ ДИАЛОГОВ/ЧАТОВ 
@router.callback_query(bst.start, F.data == "start_conversation")
async def cmd_start_conversation(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data
    await state.set_state(bst.conversation_menu)
    await callback.message.edit_text(start_conversation_msg, reply_markup=start_conversation_keyboard())
    await callback.answer()
#ВЫБОР РЕЖИМА
@router.callback_query(bst.conversation_menu, F.data == "choose_mode")
async def cmd_choose_mode(callback: CallbackQuery, state: FSMContext):
    await state.set_state(bst.choose_mode)
    text, kb = await render_prompts(callback.from_user.id)  # ← живая клавиатура prompts_kb
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
#НОВЫЙ ДИАЛОГ/ЧАТ
@router.callback_query(bst.conversation_menu, F.data == "new_conversation")
async def cmd_new_conversation(callback: CallbackQuery, state: FSMContext):
    await storage.create_chat(callback.from_user.id)
    await state.set_state(bst.new_conversation)
    text, kb = await render_chats(callback.from_user.id)   # ← живая клавиатура chats_kb
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Чат создан")
#ПРЕДЫДУЩИЕ ДИАЛОГИ/ЧАТЫ
@router.callback_query(bst.conversation_menu, F.data == "previous_conversations")
async def cmd_previous_conversations(callback: CallbackQuery, state: FSMContext):
    await state.set_state(bst.previous_conversations)
    text, kb = await render_chats(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.message(RenameForm.waiting_title, F.text)
async def apply_rename(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("rename_chat_id")
    page = data.get("rename_page", 0)
    await state.clear()

    title = message.text.strip()[:50]
    if chat_id is not None and title:
        await storage.rename_chat(message.from_user.id, chat_id, title)

    text, kb = await render_chats(message.from_user.id, page)
    await message.answer(text, reply_markup=kb)

#ВЫЙТИ НАЗАД
@router.callback_query(F.data.in_({"back", "goback", "back_to_start"}))
async def cb_back(callback: CallbackQuery, state: FSMContext):
    current = await state.get_state()          # например "Botstate:settings"
    route = BACK_ROUTES.get(current)
    if route is None:
        return await callback.answer()         # уже в главном меню — ничего не делаем
    parent_state, text, keyboard = route
    await state.set_state(parent_state)
    await callback.message.edit_text(text, reply_markup=keyboard())
    await callback.answer()     