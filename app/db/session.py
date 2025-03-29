import sqlite3
from contextlib import contextmanager
from queue import Queue
from threading import Lock
from app.core.config import settings

# 连接池
connection_pool = Queue(maxsize=settings.MAX_CONNECTIONS)
init_lock = Lock()

def init_connection_pool():
    """初始化连接池"""
    with init_lock:
        if connection_pool.empty():
            for _ in range(settings.MAX_CONNECTIONS):
                conn = sqlite3.connect(settings.DB_FILE, check_same_thread=False)
                conn.execute("PRAGMA foreign_keys = ON")
                conn.row_factory = sqlite3.Row
                connection_pool.put(conn)

@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    init_connection_pool()
    conn = connection_pool.get()
    try:
        yield conn
    finally:
        connection_pool.put(conn)

@contextmanager
def get_db_cursor():
    """获取数据库游标的上下文管理器"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e 