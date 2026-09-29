from aiogram.fsm.state import State, StatesGroup

class Botstate(StatesGroup):
    start = State()
    help = State()
    settings = State()
    choose_llm = State()
    set_prompt = State()
    create_prompt = State()
    conversation_menu = State()
    choose_mode = State()
    new_conversation = State()
    previous_conversations = State()

class PromptForm(StatesGroup):
    waiting_text = State()