from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



async def get_steam_item_kb(url: str) -> InlineKeyboardMarkup:
    keyboard = None

    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text = "Открыть в Steam", url = url)]])

    except:
        keyboard = None

    return keyboard