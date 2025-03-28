from celery import Celery
from celery.backends.database import retry
from celery.schedules import crontab
from sqlalchemy import select, delete, insert, or_, func
from db import URLAddresses, ExpiredURLHistory, get_async_session, sync_session
from config import DATABASE_URL_SYNC
import logging
import os

os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

celery = Celery(
    'delete_expired',
    broker='redis://localhost:6379',
    backend='redis://localhost:6379'
)


@celery.task
def delete_expired(n_days_expired=30):
    """
    Функция для удаления истекших ссылок, а также для удаления неиспользуемых ссылок:
        - n_days_expired: число дней, после которых url удаляются из БД
    """
    logging.info("Task 'delete_expired' started successfully!")
    print("Task 'delete_expired' started successfully!")

    with sync_session() as session:  # Получаем асинхронную сессию
        # Добавляем все истекшие ссылки в таблицу с url
        query = select(URLAddresses).where(
            or_(
                URLAddresses.expires_at <= func.now(),
                func.extract('day', (func.now() - URLAddresses.created_at)) > n_days_expired
            )
        )
        records_to_insert = session.execute(query)
        records_to_insert = records_to_insert.scalars().all()

        if records_to_insert:
            for record in records_to_insert:
                values_to_insert = {
                    'user_id': record.user_id,
                    'initial_url': record.initial_url,
                    'shorten_url': record.shorten_url,
                    'open_url_count': record.open_url_count,
                    'created_at': record.created_at,
                    'last_used_at': record.last_used_at,
                    'expired_at': record.expires_at
                }

                # Записываем данные в БД
                try:
                    query = insert(ExpiredURLHistory).values(**values_to_insert)
                    session.execute(query)
                    session.commit()
                except Exception as e:
                    logging.error(f"Error inserting data: {e}")

            # Удаляем все ссылки, срок действия которых истек
            try:
                query = delete(URLAddresses).where(
                    or_(
                        URLAddresses.expires_at <= func.now(),
                        func.extract('day', (func.now() - URLAddresses.created_at)) > n_days_expired
                    )
                )
                session.execute(query)
                session.commit()
            except Exception as e:
                logging.error(f"Error deleting expired URLs: {e}")




# celery -A task:celery worker --beat --loglevel=info
# celery -A task:celery worker  --loglevel=info
# celery -A task:celery beat --loglevel=info