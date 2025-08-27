# This technically uses the same service as established for Trulens, hence the ENVs.

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from fastapi.logger import logger
import os

# Initialize pool once (Singleton)
_pool = None


def init_db_pool():
    global _pool

    _pool = ConnectionPool(
        f"""host={os.getenv("TRULENS_HOST")} dbname={os.getenv("APP_DB")} user={os.getenv("TRULENS_USER")} password={os.getenv("TRULENS_PASSWORD")} port={os.getenv("TRULENS_PORT")}""",
        kwargs={"row_factory": dict_row},
        min_size=1,
        max_idle=60 * 5,  # in seconds, so 5 minutes
    )
    if _pool is None:
        logger.error("Failed to create Postgres connection pool")
    else:
        logger.info("Postgres connection pool created successfully")


def get_pg_connection():
    """
    Gets a database connection from the pool.
    Use like this to ensure connection is returned to the pool:
    >>> with get_pg_connection() as conn:
    >>>    with conn.cursor() as cur:
    >>>        cur.execute("SELECT 1")
    >>>        ...
    """
    if _pool is None:
        init_db_pool()
    return _pool.connection()


def close_db_pool():
    if _pool is not None:
        _pool.close()
        _pool = None
        logger.info("Postgres connection pool closed")
