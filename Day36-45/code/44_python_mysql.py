"""
Day 44 - Python接入MySQL数据库

Covers:
  1. pymysql 原生操作 (DDL / CRUD / 事务 / 批量插入 / 分页查询)
  2. SQLAlchemy ORM 模型定义与 CRUD
  3. 企业级 DatabaseHelper 封装 (连接池 / 上下文管理 / 类型提示)

Comparison: Python pymysql vs C++ MySQL Connector
--------------------------------------------------
| Feature                | Python pymysql               | C++ MySQL Connector          |
|------------------------|------------------------------|------------------------------|
| Language               | Pure Python                  | C++ (link libmysqlclient)    |
| Install                | pip install pymysql          | cmake / vcpkg / apt          |
| Connection API         | pymysql.connect(...)         | sql::mysql::MySQL_Driver     |
| Query Execution        | cursor.execute(sql, args)    | stmt->executeQuery(sql)      |
| Parameter Binding      | %s placeholders (DB-API 2.0) | PreparedStatement with ?     |
| Result Fetch           | fetchone / fetchall          | ResultSet->next() loop       |
| ORM Support            | SQLAlchemy, Django           | None built-in                |
| Async Support          | aiomysql (third-party)       | Not natively                 |
| Performance            | Adequate for most apps       | Faster for CPU-bound loads   |
| Deployment             | Cross-platform, no compile   | Requires C++ toolchain       |

Requirements:
    pip install pymysql cryptography sqlalchemy
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator, Optional, Sequence

import pymysql
from pymysql.cursors import DictCursor
from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine, text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
    sessionmaker,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection defaults (override via env vars or constructor args in production)
# ---------------------------------------------------------------------------
DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 3306
DEFAULT_USER: str = "guest"
DEFAULT_PASSWORD: str = "Guest.618"
DEFAULT_DATABASE: str = "hrs"
DEFAULT_CHARSET: str = "utf8mb4"


# =============================================================================
# Part 1 — pymysql 原生操作
# =============================================================================


def create_connection(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    user: str = DEFAULT_USER,
    password: str = DEFAULT_PASSWORD,
    database: str = DEFAULT_DATABASE,
    charset: str = DEFAULT_CHARSET,
    autocommit: bool = False,
) -> pymysql.Connection:
    """Create and return a pymysql Connection."""
    conn: pymysql.Connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset=charset,
        autocommit=autocommit,
    )
    logger.info("Connected to MySQL %s@%s:%s/%s", user, host, port, database)
    return conn


# -- DDL --------------------------------------------------------------------

DDL_DEPT: str = """
CREATE TABLE IF NOT EXISTS `tb_dept` (
    `dno`    INT         NOT NULL PRIMARY KEY,
    `dname`  VARCHAR(20) NOT NULL,
    `dloc`   VARCHAR(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

DDL_EMP: str = """
CREATE TABLE IF NOT EXISTS `tb_emp` (
    `eno`    INT         NOT NULL PRIMARY KEY,
    `ename`  VARCHAR(20) NOT NULL,
    `job`    VARCHAR(20) NOT NULL,
    `mgr`    INT,
    `sal`    DECIMAL(10,2) NOT NULL,
    `comm`   DECIMAL(10,2),
    `dno`    INT,
    FOREIGN KEY (`dno`) REFERENCES `tb_dept`(`dno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def init_schema(conn: pymysql.Connection) -> None:
    """Execute DDL to ensure tables exist."""
    with conn.cursor() as cursor:
        cursor.execute(DDL_DEPT)
        cursor.execute(DDL_EMP)
    conn.commit()
    logger.info("Schema initialised (tb_dept, tb_emp)")


# -- CRUD helpers -----------------------------------------------------------


def insert_dept(conn: pymysql.Connection, dno: int, dname: str, dloc: str) -> int:
    """Insert a department row.  Returns affected row count."""
    with conn.cursor() as cursor:
        affected: int = cursor.execute(
            "INSERT INTO `tb_dept` VALUES (%s, %s, %s)", (dno, dname, dloc)
        )
    conn.commit()
    return affected


def insert_many_depts(
    conn: pymysql.Connection, rows: Sequence[tuple[int, str, str]]
) -> int:
    """Batch-insert departments using executemany."""
    with conn.cursor() as cursor:
        affected: int = cursor.executemany(
            "INSERT INTO `tb_dept` VALUES (%s, %s, %s)", list(rows)
        )
    conn.commit()
    return affected


def update_dept(conn: pymysql.Connection, dno: int, dname: str, dloc: str) -> int:
    with conn.cursor() as cursor:
        affected: int = cursor.execute(
            "UPDATE `tb_dept` SET `dname`=%s, `dloc`=%s WHERE `dno`=%s",
            (dname, dloc, dno),
        )
    conn.commit()
    return affected


def delete_dept(conn: pymysql.Connection, dno: int) -> int:
    with conn.cursor() as cursor:
        affected: int = cursor.execute(
            "DELETE FROM `tb_dept` WHERE `dno`=%s", (dno,)
        )
    conn.commit()
    return affected


def fetch_all_depts(conn: pymysql.Connection) -> list[dict[str, Any]]:
    """Fetch all departments as list of dicts."""
    with conn.cursor(DictCursor) as cursor:
        cursor.execute("SELECT `dno`, `dname`, `dloc` FROM `tb_dept`")
        return cursor.fetchall()  # type: ignore[return-value]


def fetch_emps_page(
    conn: pymysql.Connection, page: int = 1, size: int = 10
) -> list[dict[str, Any]]:
    """Paginated employee query ordered by salary descending."""
    offset: int = (page - 1) * size
    with conn.cursor(DictCursor) as cursor:
        cursor.execute(
            "SELECT `eno`, `ename`, `job`, `sal` "
            "FROM `tb_emp` ORDER BY `sal` DESC LIMIT %s, %s",
            (offset, size),
        )
        return cursor.fetchall()  # type: ignore[return-value]


# -- Transaction demo (explicit commit / rollback) -------------------------


def transfer_employee(
    conn: pymysql.Connection, eno: int, new_dno: int
) -> None:
    """Move an employee to another department inside a transaction."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE `tb_emp` SET `dno`=%s WHERE `eno`=%s", (new_dno, eno)
            )
        conn.commit()
        logger.info("Employee %d transferred to dept %d", eno, new_dno)
    except pymysql.MySQLError as exc:
        conn.rollback()
        logger.error("Transfer failed, rolled back: %s", exc)
        raise


# =============================================================================
# Part 2 — SQLAlchemy ORM
# =============================================================================


class Base(DeclarativeBase):
    """Declarative base for ORM models."""
    pass


class Dept(Base):  # type: ignore[misc]
    __tablename__ = "tb_dept"

    dno: Mapped[int] = mapped_column(Integer, primary_key=True)
    dname: Mapped[str] = mapped_column(String(20), nullable=False)
    dloc: Mapped[str] = mapped_column(String(30), nullable=False)

    employees: Mapped[list["Emp"]] = relationship(back_populates="department")

    def __repr__(self) -> str:
        return f"Dept(dno={self.dno!r}, dname={self.dname!r}, dloc={self.dloc!r})"


class Emp(Base):  # type: ignore[misc]
    __tablename__ = "tb_emp"

    eno: Mapped[int] = mapped_column(Integer, primary_key=True)
    ename: Mapped[str] = mapped_column(String(20), nullable=False)
    job: Mapped[str] = mapped_column(String(20), nullable=False)
    mgr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sal: Mapped[float] = mapped_column(Float, nullable=False)
    comm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dno: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tb_dept.dno"), nullable=True)

    department: Mapped[Optional["Dept"]] = relationship(back_populates="employees")

    def __repr__(self) -> str:
        return f"Emp(eno={self.eno!r}, ename={self.ename!r}, job={self.job!r})"


def build_engine(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    user: str = DEFAULT_USER,
    password: str = DEFAULT_PASSWORD,
    database: str = DEFAULT_DATABASE,
) -> Any:
    """Return a SQLAlchemy Engine connected to MySQL."""
    url: str = (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        f"?charset={DEFAULT_CHARSET}"
    )
    engine = create_engine(url, echo=False, pool_size=5, max_overflow=10)
    logger.info("SQLAlchemy engine created for %s@%s:%s/%s", user, host, port, database)
    return engine


SessionLocal = sessionmaker()


def init_orm_tables(engine: Any) -> None:
    """Create ORM-mapped tables if they do not exist."""
    Base.metadata.create_all(engine)
    logger.info("ORM tables ensured via metadata.create_all()")


def orm_demo(engine: Any) -> None:
    """Demonstrate ORM CRUD operations."""
    SessionLocal.configure(bind=engine)

    with SessionLocal() as session:
        # INSERT
        dept = Dept(dno=90, dname="Research", dloc="Beijing")
        session.add(dept)
        session.commit()
        logger.info("Inserted via ORM: %s", dept)

        # SELECT
        result: Dept | None = session.get(Dept, 90)
        logger.info("Loaded via ORM: %s", result)

        # UPDATE
        if result:
            result.dloc = "Shanghai"
            session.commit()
            logger.info("Updated dloc to Shanghai")

        # DELETE
        if result:
            session.delete(result)
            session.commit()
            logger.info("Deleted dept 90")

        # Query with filter
        depts: list[Dept] = session.query(Dept).filter(Dept.dno < 20).all()
        for d in depts:
            logger.info("  %s", d)


# =============================================================================
# Part 3 — Enterprise DatabaseHelper Class
# =============================================================================


@dataclass
class DBConfig:
    """Typed configuration for database connections."""
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    user: str = DEFAULT_USER
    password: str = DEFAULT_PASSWORD
    database: str = DEFAULT_DATABASE
    charset: str = DEFAULT_CHARSET
    autocommit: bool = False
    pool_size: int = 5


class DatabaseHelper:
    """
    Enterprise-grade MySQL helper.

    Features:
      - Context manager protocol (__enter__ / __exit__)
      - Typed execute / fetch_one / fetch_all / execute_many
      - Automatic transaction management (commit on success, rollback on error)
      - Safe parameterised queries (no SQL injection)

    Usage:
        cfg = DBConfig(database="hrs")
        with DatabaseHelper(cfg) as db:
            rows = db.fetch_all("SELECT * FROM tb_dept")
    """

    def __init__(self, config: DBConfig) -> None:
        self._config: DBConfig = config
        self._conn: Optional[pymysql.Connection] = None

    # -- Context manager ----------------------------------------------------

    def __enter__(self) -> "DatabaseHelper":
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        if self._conn is not None:
            try:
                if exc_type is None:
                    self._conn.commit()
                else:
                    self._conn.rollback()
                    logger.warning("Transaction rolled back due to: %s", exc_val)
            finally:
                self.close()
        return False  # do not suppress exceptions

    # -- Connection lifecycle -----------------------------------------------

    def connect(self) -> None:
        if self._conn is not None:
            return
        self._conn = pymysql.connect(
            host=self._config.host,
            port=self._config.port,
            user=self._config.user,
            password=self._config.password,
            database=self._config.database,
            charset=self._config.charset,
            autocommit=self._config.autocommit,
        )
        logger.info("DatabaseHelper connected to %s/%s", self._config.host, self._config.database)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.info("DatabaseHelper connection closed")

    # -- Query helpers ------------------------------------------------------

    def execute(self, sql: str, args: Optional[Sequence[Any]] = None) -> int:
        """Execute a write statement.  Returns affected row count."""
        assert self._conn is not None, "Not connected — call connect() first"
        with self._conn.cursor() as cursor:
            affected: int = cursor.execute(sql, args)
        return affected

    def execute_many(self, sql: str, args_seq: Sequence[Sequence[Any]]) -> int:
        """Execute a batch write statement.  Returns affected row count."""
        assert self._conn is not None, "Not connected — call connect() first"
        with self._conn.cursor() as cursor:
            affected: int = cursor.executemany(sql, list(args_seq))
        return affected

    def fetch_one(
        self, sql: str, args: Optional[Sequence[Any]] = None
    ) -> Optional[dict[str, Any]]:
        """Fetch a single row as a dict (or None if no rows)."""
        assert self._conn is not None
        with self._conn.cursor(DictCursor) as cursor:
            cursor.execute(sql, args)
            return cursor.fetchone()  # type: ignore[return-value]

    def fetch_all(
        self, sql: str, args: Optional[Sequence[Any]] = None
    ) -> list[dict[str, Any]]:
        """Fetch all matching rows as a list of dicts."""
        assert self._conn is not None
        with self._conn.cursor(DictCursor) as cursor:
            cursor.execute(sql, args)
            return cursor.fetchall()  # type: ignore[return-value]

    def fetch_page(
        self,
        sql: str,
        page: int = 1,
        size: int = 10,
        args: Optional[Sequence[Any]] = None,
    ) -> list[dict[str, Any]]:
        """Append LIMIT/OFFSET to *sql* for pagination and fetch all."""
        paged_sql: str = f"{sql} LIMIT %s, %s"
        offset: int = (page - 1) * size
        merged_args: list[Any] = list(args or []) + [offset, size]
        return self.fetch_all(paged_sql, merged_args)


# =============================================================================
# __main__ — runnable demo
# =============================================================================


def _demo_pymysql_raw() -> None:
    """Walk through basic pymysql CRUD operations."""
    print("\n" + "=" * 60)
    print("Part 1: pymysql Raw Operations")
    print("=" * 60)

    conn = create_connection(autocommit=True)
    try:
        init_schema(conn)

        # Insert
        insert_dept(conn, 50, "R&D", "Shenzhen")
        print("[insert] dept 50 inserted")

        # Batch insert
        batch = [(51, "Sales", "Guangzhou"), (52, "Finance", "Beijing")]
        count = insert_many_depts(conn, batch)
        print(f"[batch insert] {count} rows inserted")

        # Update
        update_dept(conn, 50, "Research", "Shanghai")
        print("[update] dept 50 updated")

        # Select all
        depts = fetch_all_depts(conn)
        print("[select all] departments:")
        for row in depts:
            print(f"  {row}")

        # Delete
        delete_dept(conn, 50)
        print("[delete] dept 50 deleted")

        # Paginated employees (table may be empty)
        page_rows = fetch_emps_page(conn, page=1, size=5)
        print(f"[page query] first page ({len(page_rows)} rows):")
        for row in page_rows:
            print(f"  {row}")
    finally:
        conn.close()
        print("[connection closed]")


def _demo_orm() -> None:
    """Demonstrate SQLAlchemy ORM operations."""
    print("\n" + "=" * 60)
    print("Part 2: SQLAlchemy ORM")
    print("=" * 60)

    engine = build_engine()
    init_orm_tables(engine)
    orm_demo(engine)
    engine.dispose()


def _demo_helper() -> None:
    """Demonstrate the enterprise DatabaseHelper class."""
    print("\n" + "=" * 60)
    print("Part 3: Enterprise DatabaseHelper")
    print("=" * 60)

    cfg = DBConfig(database=DEFAULT_DATABASE)
    with DatabaseHelper(cfg) as db:
        # Fetch departments
        rows: list[dict[str, Any]] = db.fetch_all(
            "SELECT `dno`, `dname`, `dloc` FROM `tb_dept`"
        )
        print(f"[helper] all depts ({len(rows)} rows):")
        for row in rows:
            print(f"  {row}")

        # Paginated employees
        emp_page: list[dict[str, Any]] = db.fetch_page(
            "SELECT `eno`, `ename`, `job`, `sal` FROM `tb_emp` ORDER BY `sal` DESC",
            page=1,
            size=5,
        )
        print(f"[helper] employee page ({len(emp_page)} rows):")
        for row in emp_page:
            print(f"  {row}")

    # Exiting the `with` block auto-commits (or rolls back on exception).


if __name__ == "__main__":
    _demo_pymysql_raw()
    _demo_orm()
    _demo_helper()
