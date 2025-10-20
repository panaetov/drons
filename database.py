import datetime
import logging
from contextlib import contextmanager

import psycopg2
import psycopg2.pool
import psycopg2.extras
import pydantic

logger = logging.getLogger(__name__)


DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'drones',
    'user': 'dude',
    'password': 'dude'
}

connection_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    **DB_CONFIG
)
if connection_pool:
    logger.info("Pool is created...")


@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = connection_pool.getconn()
        if conn is None:
            raise RuntimeError("Не удалось получить соединение из пула")
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Ошибка в транзакции: {e}")
        raise
    finally:
        if conn:
            conn.rollback()
            connection_pool.putconn(conn)


class BeaconDetection(pydantic.BaseModel):
    beacon_id: str
    saved_at: datetime.datetime
    receiver_id: str
    receiver_lat: float
    receiver_lon: float
    toa: int
    tos: int

    @classmethod
    def filter_last_detections(cls, beacon_id):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(
                    """
                    select beacon_id, tos, count(distinct receiver_id)
                    from beacon_detections where beacon_id = %s
                    group by beacon_id, tos
                    having count(distinct receiver_id) >= 3
                    order by tos desc
                    limit 1
                    """,
                    (beacon_id,),
                )
                row = cur.fetchone()
                if not row:
                    return []

                last_tos = row['tos']

                cur.execute(
                    """
                    select *
                    from beacon_detections where beacon_id = %s and tos = %s
                    """,
                    (beacon_id, last_tos),
                )
                rows = cur.fetchall()
                return [cls(**r) for r in rows]

    def save(self):
        logger.debug(f"Saving detection: {self}")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO beacon_detections (
                        beacon_id, saved_at,
                        receiver_id, receiver_lat, receiver_lon,
                        toa, tos
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    self.beacon_id,
                    self.saved_at,
                    self.receiver_id,
                    self.receiver_lat,
                    self.receiver_lon,
                    self.toa,
                    self.tos,
                ))
                conn.commit()
