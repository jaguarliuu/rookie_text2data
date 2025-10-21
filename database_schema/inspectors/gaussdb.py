# database_schema/inspectors/gaussdb.py
from sqlalchemy.sql import text
from sqlalchemy.engine import reflection
from .base import BaseInspector
from urllib.parse import quote_plus

# 导入 GaussDB 自定义方言以注册到 SQLAlchemy
try:
    from utils.gaussdb_dialect import GaussDBDialect
except ImportError:
    pass  # 如果导入失败,使用标准 PostgreSQL 方言

class GaussDBInspector(BaseInspector):
    """华为高斯数据库(GaussDB) 元数据获取实现

    GaussDB 兼容 PostgreSQL 协议，但在认证机制上有差异
    主要区别：
    1. 使用 SCRAM-SHA-256 认证而非 MD5
    2. 需要特殊的连接参数来禁用 SASL 检查
    3. 部分系统表路径可能不同
    """

    def __init__(self, host: str, port: int, database: str,
                username: str, password: str, schema_name: str = None, **kwargs):
        super().__init__(host, port, database, username, password, schema_name)
        self.schema_name = schema_name or "public"

    def build_conn_str(self, host: str, port: int, database: str,
                     username: str, password: str) -> str:
        """构建高斯数据库连接字符串

        关键参数说明：
        - sslmode=disable: 禁用 SSL
        - 保留 SCRAM-SHA-256 等认证方式的支持
        """
        encoded_password = quote_plus(password)
        encoded_username = quote_plus(username)

        # 构建基础连接字符串,使用自定义的 gaussdb 方言
        base_uri = f"gaussdb+psycopg://{encoded_username}:{encoded_password}@{host}:{port}/{database}"

        # 只禁用 SSL，保留 SCRAM-SHA-256 认证支持
        conn_params = "?sslmode=disable"

        return base_uri + conn_params

    def get_table_names(self, inspector: reflection.Inspector) -> list[str]:
        """获取指定 schema 下的所有表名"""
        return inspector.get_table_names(schema=self.schema_name)

    def get_table_comment(self, inspector: reflection.Inspector,
                        table_name: str) -> str:
        """获取表注释

        GaussDB 使用与 PostgreSQL 相同的系统目录结构
        """
        with self.engine.connect() as conn:
            sql = text("""
                SELECT obj_description(c.oid, 'pg_class')
                FROM pg_catalog.pg_class c
                LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = :schema AND c.relname = :table
            """)
            result = conn.execute(sql, {
                "schema": self.schema_name,
                "table": table_name
            }).scalar()
            return result or ""

    def get_column_comment(self, inspector: reflection.Inspector,
                         table_name: str, column_name: str) -> str:
        """获取列注释"""
        with self.engine.connect() as conn:
            sql = text("""
                SELECT pg_catalog.col_description(c.oid, a.attnum)
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
                WHERE n.nspname = :schema
                AND c.relname = :table
                AND a.attname = :column
                AND a.attnum > 0
                AND NOT a.attisdropped
            """)
            result = conn.execute(sql, {
                "schema": self.schema_name,
                "table": table_name,
                "column": column_name
            }).scalar()
            return result or ""

    def normalize_type(self, raw_type: str) -> str:
        """标准化字段类型

        GaussDB 支持 PostgreSQL 类型 + 部分扩展类型
        """
        type_map = {
            # PostgreSQL 标准类型
            'jsonb': 'JSON',
            'bytea': 'BLOB',
            'serial': 'INTEGER',
            'bigserial': 'BIGINT',
            'uuid': 'UUID',
            'int4': 'INTEGER',
            'int8': 'BIGINT',
            'int2': 'SMALLINT',
            'float4': 'FLOAT',
            'float8': 'DOUBLE',
            'bool': 'BOOLEAN',
            'timestamptz': 'TIMESTAMP WITH TIME ZONE',
            'timestamp': 'TIMESTAMP',

            # GaussDB 扩展类型
            'clob': 'TEXT',
            'blob': 'BLOB',
            'number': 'NUMERIC',
            'raw': 'BYTEA',
            'nvarchar2': 'NVARCHAR',
            'varchar2': 'VARCHAR'
        }

        # 提取基础类型（去除长度限制）
        base_type = raw_type.split('(')[0].lower().strip()
        return type_map.get(base_type, raw_type.upper())
