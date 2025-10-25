import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from llm_handler import get_gpt4o_response, get_llama_response
from config import get_config

from static import texts

config = get_config()
bot = Bot(token=config["tg_token"])
dp = Dispatcher()

current_model = ""

last_gpt4o_response = {"text": None, "source": None}
last_llama_response = {"text": None, "source": None}


@dp.message(CommandStart())
async def start_command(message: Message) -> None:
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение и инструкции.
    """
    await message.answer(texts.START_TEXT)


@dp.message(Command("setmodel"))
async def set_model(message: Message) -> None:
    """
    Обработчик команды /setmodel <имя_модели>.
    Позволяет пользователю выбрать активную модель (GPT-4o или LLaMA).
    """
    global current_model
    parts = message.text.split()
    model = parts[1].lower() if len(parts) > 1 else ""

    if model in ["gpt4o", "llama"]:
        current_model = model
        await message.answer(texts.MODEL_CHANGED.format(model_name=model.upper()))
    else:
        await message.answer(texts.UNKNOWN_MODEL)


@dp.message()
async def handle_text(message: Message) -> None:
    """
    Обработка текстовых сообщений от пользователя.
    Делает запрос к выбранной модели и выводит результат анализа эмоций.
    """
    global last_gpt4o_response, last_llama_response, current_model
    text = message.text.strip()

    if not text:
        await message.answer(texts.ERROR_MESSAGE.format(error="Пустое сообщение."))
        return

    wait_msg = await message.answer(texts.WAIT_MESSAGE)

    try:
        if current_model == "gpt4o":
            response = await asyncio.wait_for(get_gpt4o_response(text), timeout=60)
            last_gpt4o_response = {"text": response, "source": text}
        elif current_model == "llama":
            response = await asyncio.wait_for(get_llama_response(text), timeout=60)
            last_llama_response = {"text": response, "source": text}
        else:
            await wait_msg.edit_text(texts.UNKNOWN_MODEL)
            return

        if response:
            await wait_msg.edit_text(f"Анализ ({current_model.upper()}):\n\n{response}")
        else:
            await wait_msg.edit_text(texts.ERROR_MESSAGE.format(error="Ошибка на стороне API."))

    except asyncio.TimeoutError:
        await wait_msg.edit_text(texts.TIMEOUT_MESSAGE)
    except Exception as e:
        await wait_msg.edit_text(texts.ERROR_MESSAGE.format(error=str(e)))



async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
