# utils/database.py
import aiosqlite
import logging
import datetime

DATABASE_NAME = 'violations.db'

async def setup_db():
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_link_violations (
                user_id INTEGER PRIMARY KEY,
                violations INTEGER DEFAULT 0,
                last_violation_timestamp TEXT
            )
        ''')
        await db.commit()
    logging.info("Database setup complete.")

async def get_user_violations(user_id):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute("SELECT violations, last_violation_timestamp FROM user_link_violations WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return {"violations": row[0], "last_violation_timestamp": row[1]}
        return None

async def update_user_violations(user_id, violations, timestamp):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_link_violations (user_id, violations, last_violation_timestamp) VALUES (?, ?, ?)",
            (user_id, violations, timestamp)
        )
        await db.commit()

async def reset_user_violations(user_id):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("UPDATE user_link_violations SET violations = 0, last_violation_timestamp = NULL WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_all_violations():
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute("SELECT user_id, violations, last_violation_timestamp FROM user_link_violations")
        return await cursor.fetchall()

# You can add more database functions here as needed, e.g., for reporting.