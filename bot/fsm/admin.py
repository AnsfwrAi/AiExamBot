from aiogram.filters.state import State, StatesGroup

class AdminPaymentCheck(StatesGroup):
    waiting_for_accept = State()
    redis_key = State()
