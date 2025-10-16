# database_schema/inspectors/dm.py
from sqlalchemy.sql import text
from sqlalchemy.engine import reflection
from .base import BaseInspector
from urllib.parse import quote_plus

class DMInspector(BaseInspector):
    """达梦数据库（DM Database）元数据获取实现

    达梦数据库特点：
    1. 国产数据库，部分兼容 Oracle 语法
    2. 使用 dmPython 驱动
    3. 默认端口：5236
    4. 支持 Schema 概念，类似 Oracle
    5. 表名和列名默认大写
    """

    def __init__(self, host: str, port: int, database: str,
                username: str, password: str, schema_name: str = None, **kwargs):
        super().__init__(host, port, database, username, password, schema_name)
        # 达梦 schema 通常与用户名一致，且默认大写
        # 如果提供了 schema_name，使用它；否则使用用户名
        self.schema_name = (schema_name or username).upper()

    def build_conn_str(self, host: str, port: int, database: str,
                     username: str, password: str) -> str:
        """构建达梦数据库连接字符串

        达梦连接格式：dm+dmPython://username:password@host:port/?schema=SCHEMANAME
        """
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)

        # 达梦数据库连接字符串
        # 注意：达梦的连接方式类似 Oracle
        return f"dm+dmPython://{encoded_username}:{encoded_password}@{host}:{port}/"

    def get_table_names(self, inspector: reflection.Inspector) -> list[str]:
        """获取指定 schema 下的所有表名"""
        return inspector.get_table_names(schema=self.schema_name)

    def get_table_comment(self, inspector: reflection.Inspector,
                        table_name: str) -> str:
        """获取表注释

        达梦使用类似 Oracle 的系统表结构
        """
        with self.engine.connect() as conn:
            sql = text("""
                SELECT COMMENTS
                FROM ALL_TAB_COMMENTS
                WHERE OWNER = :owner
                    AND TABLE_NAME = :table_name
            """)
            try:
                result = conn.execute(sql, {
                    'owner': self.schema_name,
                    'table_name': table_name.upper()
                }).scalar()
                return result or ""
            except Exception as e:
                print(f"获取表注释失败 {table_name}: {str(e)}")
                return ""

    def get_column_comment(self, inspector: reflection.Inspector,
                         table_name: str, column_name: str) -> str:
        """获取列注释"""
        with self.engine.connect() as conn:
            sql = text("""
                SELECT COMMENTS
                FROM ALL_COL_COMMENTS
                WHERE OWNER = :owner
                    AND TABLE_NAME = :table_name
                    AND COLUMN_NAME = :column_name
            """)
            try:
                result = conn.execute(sql, {
                    'owner': self.schema_name,
                    'table_name': table_name.upper(),
                    'column_name': column_name.upper()
                }).scalar()
                return result or ""
            except Exception as e:
                print(f"获取列注释失败 {table_name}.{column_name}: {str(e)}")
                return ""

    def normalize_type(self, raw_type: str) -> str:
        """标准化达梦数据类型

        达梦支持多种数据类型，部分兼容 Oracle
        """
        # 类型映射表
        type_map = {
            # 数值类型
            'NUMBER': 'NUMERIC',
            'NUMERIC': 'NUMERIC',
            'DECIMAL': 'DECIMAL',
            'INTEGER': 'INTEGER',
            'INT': 'INTEGER',
            'BIGINT': 'BIGINT',
            'SMALLINT': 'SMALLINT',
            'TINYINT': 'TINYINT',
            'FLOAT': 'FLOAT',
            'DOUBLE': 'DOUBLE',
            'REAL': 'FLOAT',

            # 字符串类型
            'VARCHAR': 'VARCHAR',
            'VARCHAR2': 'VARCHAR',
            'CHAR': 'CHAR',
            'CHARACTER': 'CHAR',
            'TEXT': 'TEXT',
            'CLOB': 'TEXT',
            'NCHAR': 'NCHAR',
            'NVARCHAR': 'NVARCHAR',
            'NVARCHAR2': 'NVARCHAR',

            # 日期时间类型
            'DATE': 'DATE',
            'TIME': 'TIME',
            'TIMESTAMP': 'TIMESTAMP',
            'DATETIME': 'DATETIME',

            # 二进制类型
            'BLOB': 'BLOB',
            'BINARY': 'BINARY',
            'VARBINARY': 'VARBINARY',
            'IMAGE': 'BLOB',

            # 其他类型
            'BIT': 'BOOLEAN',
            'BOOLEAN': 'BOOLEAN'
        }

        # 提取基础类型（去除长度、精度等）
        base_type = raw_type.split('(')[0].strip().upper()

        # 返回标准化类型
        return type_map.get(base_type, base_type)
