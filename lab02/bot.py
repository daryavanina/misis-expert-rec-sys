import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pathlib import Path
from llm_handler import get_gpt4o_response, get_llama_response, MAX_ANSWER_TIMEOUT_SECONDS
from config import get_config


config = get_config()
bot = Bot(token=config["tg_token"])
dp = Dispatcher()


def load_texts():
    static_path = Path(__file__).parent / "static" / "texts.json"
    with open(static_path, "r", encoding="utf-8") as f:
        return json.load(f)

texts = load_texts()

user_state = {}

DEFAULT_PARAMS = {
    "model": None,
    "temperature": 0.7,
    "max_tokens": 100,
    "response_language": "русский"
}


@dp.message(CommandStart())
async def start_command(message: types.Message) -> None:
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение и инструкции.
    """
    user_state[message.from_user.id] = DEFAULT_PARAMS.copy()
    await message.answer(texts["START_TEXT"])


@dp.message(Command("setmodel"))
async def choose_model(message: types.Message) -> None:
    """
    Обработчик команды /setmodel
    Позволяет пользователю выбрать активную модель (GPT-4o или LLaMA).
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="GPT-4o", callback_data="model_gpt4o")
    kb.button(text="LLaMA", callback_data="model_llama")
    await message.answer(texts["MODEL_SELECT"], reply_markup=kb.as_markup())


@dp.callback_query(lambda c: c.data.startswith("model_"))
async def set_model(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    model = callback.data.split("_")[1]
    user_state.setdefault(user_id, DEFAULT_PARAMS.copy())
    user_state[user_id]["model"] = model

    await callback.message.edit_text(
        texts["MODEL_CHANGED"].format(model_name=model.upper())
    )

    await show_param_menu(callback.message, user_id)
    
    
async def show_param_menu(message: types.Message, user_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="Температура", callback_data="param_temp")
    kb.button(text="Макс. токены", callback_data="param_tokens")
    kb.button(text="Язык ответа", callback_data="param_lang")
    kb.button(text="Всё верно", callback_data="param_done")

    params = user_state[user_id]
    await message.answer(
        texts["PARAMS_INFO"].format(**params),
        reply_markup=kb.as_markup()
    )
    
    
@dp.callback_query(lambda c: c.data == "param_temp")
async def change_temp(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    for t in [0.3, 0.5, 0.7, 1.0]:
        kb.button(text=f"{t}", callback_data=f"temp_{t}")
    await callback.message.edit_text(texts["TEMP_SELECT"], reply_markup=kb.as_markup())


@dp.callback_query(lambda c: c.data.startswith("temp_"))
async def set_temp(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    temp = float(callback.data.split("_")[1])
    user_state[user_id]["temperature"] = temp
    await show_param_menu(callback.message, user_id)
    
    
@dp.callback_query(lambda c: c.data == "param_tokens")
async def change_tokens(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    for t in [100, 300, 500, 1000]:
        kb.button(text=f"{t}", callback_data=f"tokens_{t}")
    await callback.message.edit_text(texts["TOKENS_SELECT"], reply_markup=kb.as_markup())


@dp.callback_query(lambda c: c.data.startswith("tokens_"))
async def set_tokens(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    tokens = int(callback.data.split("_")[1])
    user_state[user_id]["max_tokens"] = tokens
    await show_param_menu(callback.message, user_id)


@dp.callback_query(lambda c: c.data == "param_lang")
async def change_lang(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    for lang in ["русский", "english"]:
        kb.button(text=lang, callback_data=f"lang_{lang}")
    await callback.message.edit_text(texts["LANG_SELECT"], reply_markup=kb.as_markup())

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def set_lang(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = callback.data.split("_")[1]
    user_state[user_id]["language"] = lang
    await show_param_menu(callback.message, user_id)


@dp.callback_query(lambda c: c.data == "param_done")
async def finish_params(callback: types.CallbackQuery):
    await callback.message.edit_text(texts["PARAMS_SAVED"])


@dp.message()
async def analyze_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in user_state or not user_state[user_id]["model"]:
        await message.answer(texts["UNKNOWN_MODEL"])
        return

    wait_msg = await message.answer(texts["WAIT_MESSAGE"])
    params = user_state[user_id]

    try:
        if params["model"] == "gpt4o":
            response = await asyncio.wait_for(
                get_gpt4o_response(text, params),
                timeout=MAX_ANSWER_TIMEOUT_SECONDS
            )
        else:
            response = await asyncio.wait_for(
                get_llama_response(text, params),
                timeout=MAX_ANSWER_TIMEOUT_SECONDS
            )

        await wait_msg.edit_text(f"Анализ ({params['model'].upper()}):\n\n{response}")

    except asyncio.TimeoutError:
        await wait_msg.edit_text(texts["TIMEOUT_MESSAGE"])
    except Exception as e:
        await wait_msg.edit_text(texts["ERROR_MESSAGE"].format(error=str(e)))



async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
