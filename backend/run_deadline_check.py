#!/usr/bin/env python
"""
Deadline scheduler — deadline eslatmalarini avtomatik tekshiradi.
Her 1 soatda ishga tushiriladi.

Cron misol:
0 * * * * cd /path/to/backend && python run_deadline_check.py
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.services.services import notification_service


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


async def check_deadlines():
    """Barcha deadline larni tekshirish."""
    logger.info("Deadline tekshiruvi boshlandi...")
    
    async with SessionLocal() as db:
        result = await notification_service.check_deadline_reminders(db, days_warning=3)
        await db.commit()
        logger.info(f"Deadline tekshiruvi tugadi: {result}")

    return result


def main():
    result = asyncio.run(check_deadlines())
    logger.info(f"Yuborilgan eslatmalar: {result.get('sent_notifications', 0)}")


if __name__ == "__main__":
    main()