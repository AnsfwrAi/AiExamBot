from . import bot, dp

from . handlers import admin, main, user, user_callback, set_router

set_router()
# dp.include_router(admin)
# dp.include_router(main)
# dp.include_router(user)
# dp.include_router(user_callback)
