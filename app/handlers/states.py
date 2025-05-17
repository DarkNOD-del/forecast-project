from aiogram import Router
from aiogram.types import Message

import app.fsm as fsm
import app.text as txt


router = Router()


@router.message(fsm.State_Default.working)
async def working(message: Message):
    reply = txt.process_msg
    await message.answer(reply)