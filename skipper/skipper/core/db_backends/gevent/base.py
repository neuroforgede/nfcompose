# customized version from original file at:
# https://github.com/jneight/django-db-geventpool/blob/master/django_db_geventpool/backends/postgresql_psycopg2/base.py
# This adds gevent Timeout logic to the health check of the connection
# as well as further defensive programming to handle unexpected exceptions.

from gevent import Timeout
from skipper.environment import SKIPPER_DB_POOL_HEALTHCHECK_TIMEOUT

try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.extensions
except ImportError as e:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("Error loading psycopg2 module: %s" % e)

from django.db.backends.postgresql.base import (
    DatabaseWrapper as OriginalDatabaseWrapper,
)
import logging

from django_db_geventpool.backends import base, pool

logger = logging.getLogger(__name__)


class PostgresConnectionPool(pool.DatabaseConnectionPool):
    DBERROR = psycopg2.DatabaseError

    def __init__(self, *args, **kwargs):
        self.connect = kwargs.pop("connect", psycopg2.connect)
        self.connection = None
        maxsize = kwargs.pop("MAX_CONNS", 4)
        reuse = kwargs.pop("REUSE_CONNS", maxsize)
        self.args = args
        self.kwargs = kwargs
        self.kwargs["client_encoding"] = "UTF8"
        super().__init__(maxsize, reuse)

    def create_connection(self):
        conn = self.connect(*self.args, **self.kwargs)
        psycopg2.extras.register_default_jsonb(conn_or_curs=conn, loads=lambda x: x)
        return conn

    def check_usable(self, connection):
        timeout = Timeout(SKIPPER_DB_POOL_HEALTHCHECK_TIMEOUT)
        timeout.start()
        try:
            if connection.closed:
                # unsure if we can even reach this case here
                # but to add some extra safety we handle this case
                raise psycopg2.DatabaseError("Database connection is closed")
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            logger.exception("Database connection failed health check")
            raise psycopg2.DatabaseError("Database connection failed health check")
        except Timeout as t:
            if t is not timeout:
                logger.exception("Unexpected Timeout exception")
                raise
            logger.exception("Database connection timed out during healthcheck")
            raise psycopg2.DatabaseError("Database connection timed out during healthcheck")
        finally:
            timeout.close()


class DatabaseWrapper(base.DatabaseWrapperMixin, OriginalDatabaseWrapper):
    pool_class = PostgresConnectionPool
    INTRANS = psycopg2.extensions.TRANSACTION_STATUS_INTRANS