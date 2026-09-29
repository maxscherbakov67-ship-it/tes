from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.storage import PRESET_PROMPTS

class ChatCB(CallbackData, prefix="chat"):
    action: str
    id: int = 0
    page: int = 0

class PromptCB(CallbackData, prefix="prompt"):
    action: str
    id: int = 0
    page: int = 0

def add_pagination(builder: InlineKeyboardBuilder, page: int, pages: int, make_cb) -> None:
    if pages <= 1:
        return
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="Назад", callback_data=make_cb(page - 1)))
    nav.append(InlineKeyboardButton text=f("{page + 1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="Вперёд", callback_data=make_cb(page + 1)))
    builder.row(*nav)

def chats_kb(chats, active_id: int | None, page: int, pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for chat in chats:
        mark = "✅ " if chat["id"] == active_id else ""
        builder.row(
            InlineKeyboardButton(
                text = f"{mark}{chat["title"]}",
                callback_data=ChatCB(action="open", id= chat["id"], page=page).pack(),
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=ChatCB(action="delete", id= chat["id"], page=page).pack(),
            ),
        )
    add_pagination(builder, page, pages, lambda p: ChatCB(action="page", page=p).pack())
    builder.row(
        InlineKeyboardButton(
            text="Новый чат", callback_data=ChatCB(action="new").pack()
            )
        )
    return builder.as_markup()

def prompts_kb(customs, page: int, pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder

    for pid, (title, _) in PRESET_PROMPTS.items():
        builder.button(text=title, callback_data=PromptCB(action="preset", id=pid, page=page))
    builder.adjust(2)

    for p in customs:
        builder.row(
            InlineKeyboardButton(
                text=f"⭐ {p['title']}",
                callback_data=PromptCB(action="custom", id =p["id"], page=page).pack(),
                
                )
        )

def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
        InlineKeyboardButton(text="Перейти к чатам", callback_data="start_conversation")
        ],
        [
        InlineKeyboardButton(text="Настройки", callback_data="settings"),
        InlineKeyboardButton(text="Помощь", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def settings_keyboard() -> InlineKeyboardMarkup:
    keyboard= [
        [
        InlineKeyboardButton(text="Создать режим работы(промпт)", callback_data="set_prompt")
        ],
        [
        InlineKeyboardButton(text="Выбрать модель", callback_data="choose_llm")
        ],
        [
        InlineKeyboardButton(text="Выйти назад", callback_data="back_to_start")
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def start_conversation_keyboard() -> InlineKeyboardMarkup:
    keyboard= [
        [
        InlineKeyboardButton(text="Новый чат", callback_data="new_conversation"),
        ],
        [
        InlineKeyboardButton(text="Предыдущие чаты", callback_data="previous_conversations"),
        ],
        [
        InlineKeyboardButton(text="Выбрать режим(промпт)", callback_data="choose_mode"),
        InlineKeyboardButton(text="Выйти назад", callback_data="back_to_start"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def goback_keyboard() -> InlineKeyboardMarkup:
    keyboard= [
        [
        InlineKeyboardButton(text="Выйти назад", callback_data="goback")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def set_prompt_keyboard() -> InlineKeyboardMarkup:
    keyboard= [
        [
        InlineKeyboardButton(text="Выбрать существующий промпт", callback_data="new_conversation"),
        ],
        [
        InlineKeyboardButton(text="Создать новый промпт", callback_data="previous_conversations"),
        ],
        [
        InlineKeyboardButton(text="Выйти назад", callback_data="back_to_start"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_prompt_keyboard() -> InlineKeyboardMarkup:
    keyboard= [
        [
        InlineKeyboardButton(text="Новый чат", callback_data="new_conversation"),
        ],
        [
        InlineKeyboardButton(text="Предыдущие чаты", callback_data="previous_conversations"),
        ],
        [
        InlineKeyboardButton(text="Выбрать режим(промпт)", callback_data="choose_mode"),
        InlineKeyboardButton(text="Выйти назад", callback_data="back_to_start"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def choose_llm_keyboard() -> InlineKeyboardMarkup:
    keyboard= [
        [
        InlineKeyboardButton(text="Новый чат", callback_data="new_conversation"),
        ],
        [
        InlineKeyboardButton(text="Предыдущие чаты", callback_data="previous_conversations"),
        ],
        [
        InlineKeyboardButton(text="Выбрать режим(промпт)", callback_data="choose_mode"),
        InlineKeyboardButton(text="Выйти назад", callback_data="back_to_start"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def choose_mode_keyboard() -> InlineKeyboardMarkup:
    keyboard= [
        [
        InlineKeyboardButton(text="Новый чат", callback_data="new_conversation"),
        ],
        [
        InlineKeyboardButton(text="Предыдущие чаты", callback_data="previous_conversations"),
        ],
        [
        InlineKeyboardButton(text="Выбрать режим(промпт)", callback_data="choose_mode"),
        InlineKeyboardButton(text="Выйти назад", callback_data="back_to_start"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def new_conversation_keyboard() -> InlineKeyboardMarkup:
    keyboard= [
        [
        InlineKeyboardButton(text="Новый чат", callback_data="new_conversation"),
        ],
        [
        InlineKeyboardButton(text="Предыдущие чаты", callback_data="previous_conversations"),
        ],
        [
        InlineKeyboardButton(text="Выбрать режим(промпт)", callback_data="choose_mode"),
        InlineKeyboardButton(text="Выйти назад", callback_data="back_to_start"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def previous_conversations_keyboard() -> InlineKeyboardMarkup:
    keyboard= [
        [
        InlineKeyboardButton(text="Новый чат", callback_data="new_conversation"),
        ],
        [
        InlineKeyboardButton(text="Предыдущие чаты", callback_data="previous_conversations"),
        ],
        [
        InlineKeyboardButton(text="Выбрать режим(промпт)", callback_data="choose_mode"),
        InlineKeyboardButton(text="Выйти назад", callback_data="back_to_start"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def start_conversation_() -> InlineKeyboardMarkup:
    keyboard= [
        [
        InlineKeyboardButton(text="Новый чат", callback_data="new_conversation"),
        ],
        [
        InlineKeyboardButton(text="Предыдущие чаты", callback_data="previous_conversations"),
        ],
        [
        InlineKeyboardButton(text="Выбрать режим(промпт)", callback_data="choose_mode"),
        InlineKeyboardButton(text="Выйти назад", callback_data="back_to_start"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)