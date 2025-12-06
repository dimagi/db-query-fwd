"""Custom logging handlers."""

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


class DatabaseHandler(logging.Handler):

    def __init__(self, db_url):
        super().__init__()
        self.engine = create_engine(db_url)
        self._ensure_table()

    def _ensure_table(self):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS dqf_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level VARCHAR(10),
            message TEXT
        )
        """

        with self.engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()

    def emit(self, record):
        insert_sql = """
        INSERT INTO dqf_logs (level, message)
        VALUES (:level, :message)
        """

        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text(insert_sql),
                    {'level': record.levelname, 'message': self.format(record)},
                )
                conn.commit()
        except SQLAlchemyError:
            self.handleError(record)
