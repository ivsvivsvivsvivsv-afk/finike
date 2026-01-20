import logging
import os
import asyncio

from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН_ТУТ")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Бот жив, webhook работает")


async def handle_webhook(request: web.Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot, update)
    return web.Response(text="OK")


async def main():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

    logger.info("Server started on 0.0.0.0:8000 /webhook")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
