from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, StateFilter

import app.fsm as fsm
import app.text as txt
import app.config as cfg
import app.keyboards as kb
import app.modules.steam as steam
import app.modules.forecaster as forecaster


router = Router()



@router.message(StateFilter(None), CommandStart())
async def start(message: Message):
    reply = txt.start_msg.format(name = message.from_user.first_name)
    await message.answer(reply)



@router.message(StateFilter(None), F.text.startswith(cfg.STEAM_MARKETPLACE_TEMPLATE))
async def work(message: Message, state: FSMContext):
    await state.set_state(fsm.State_Default.working)
    await message.answer(txt.begin_msg)


    status, steam_item = await steam.get_steam_item_from_url(message.text)

    if status != "ok":
        await raise_error(message, state, status)
        return
    

    status, forecast = await forecaster.get_forecast(steam_item.price_history)

    if status != "ok":
        await raise_error(message, state, status)
        return
    

    reply = f"*{steam_item.market_hash_name.upper()}*" + "\n"
    reply += f"Тип: {steam_item.type}" + "\n"
    reply += f"Продажи: {len(steam_item.price_history)} шт." + "\n\n"
    reply += f"Прогноз:" + "\n"

    for day in forecast:
        reply += f"{day['date']} - {day['value']} руб." + "\n"

    reply_markup = await kb.get_steam_item_kb(steam_item.url)

    await message.answer_photo(steam_item.icon_url, reply, parse_mode = ParseMode.MARKDOWN, reply_markup = reply_markup)


    await message.answer(txt.end_msg)
    await state.clear()


    print(f"[INFO] Запрос от @{message.from_user.username} обработан: {steam_item.market_hash_name}")



async def raise_error(message: Message, state: FSMContext, status: str):
    reply = txt.error_msg.format(status = status)
    await message.answer(reply)
    await state.clear()

    print(f"[ERROR] Запрос от @{message.from_user.username} завершился с ошибкой: {status}")