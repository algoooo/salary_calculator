import asyncio
from datetime import datetime

from database import init_db
from database import session
from database.crud import users
from database.crud import workdays

async def initialize_db():
    await init_db.initialize_tables(session.get_session_factory().kw["bind"])

if __name__ == '__main__':
    asyncio.run(initialize_db())