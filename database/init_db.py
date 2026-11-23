from sqlalchemy.ext.asyncio import AsyncEngine
import database.models as models

async def initialize_tables(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all) # type: ignore


