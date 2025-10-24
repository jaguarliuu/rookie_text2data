"""
自定义达梦数据库 SQLAlchemy 方言
基于 dmPython 驱动的简化实现

注意: 达梦官方提供 sqlalchemy_dm 方言包,但需要单独安装
这是一个简化的实现,用于基本的数据库连接和查询
"""
import re
from sqlalchemy import types as sqltypes
from sqlalchemy.engine import default
from sqlalchemy.sql import compiler


class DMCompiler(compiler.SQLCompiler):
    """达梦 SQL 编译器"""
    pass


class DMTypeCompiler(compiler.GenericTypeCompiler):
    """达梦类型编译器"""
    pass


class DMDialect(default.DefaultDialect):
    """
    达梦数据库方言

    连接字符串格式:
    dm+dmPython://username:password@host:port/schema
    dm+dmPython://SYSDBA:password@localhost:5236
    """
    name = 'dm'
    driver = 'dmPython'

    # 达梦数据库特性
    supports_alter = True
    supports_sequences = True
    supports_native_boolean = False
    supports_comments = True

    # 标识符特性
    max_identifier_length = 128

    # 编译器
    statement_compiler = DMCompiler
    type_compiler = DMTypeCompiler

    # 默认参数化风格
    paramstyle = 'qmark'  # dmPython 使用 ? 作为占位符

    # 执行选项
    execution_ctx_cls = default.DefaultExecutionContext

    @classmethod
    def dbapi(cls):
        """导入 dmPython 驱动"""
        import dmPython
        return dmPython

    def create_connect_args(self, url):
        """
        从 URL 创建连接参数

        URL 格式: dm+dmPython://user:password@host:port/schema
        """
        opts = url.translate_connect_args(username='user')
        opts.update(url.query)

        # dmPython 连接参数
        connect_args = {}

        if 'user' in opts:
            connect_args['user'] = opts.pop('user')
        if 'password' in opts:
            connect_args['password'] = opts.pop('password')
        if 'host' in opts:
            connect_args['server'] = opts.pop('host')
        if 'port' in opts:
            connect_args['port'] = int(opts.pop('port'))
        if 'database' in opts:
            # database 在达梦中对应 schema
            schema = opts.pop('database')
            if schema:
                connect_args['schema'] = schema

        # 其他参数
        connect_args.update(opts)

        return ([], connect_args)

    def do_rollback(self, dbapi_connection):
        """执行回滚"""
        dbapi_connection.rollback()

    def do_commit(self, dbapi_connection):
        """执行提交"""
        dbapi_connection.commit()

    def get_schema_names(self, connection, **kw):
        """获取所有 schema 名称"""
        cursor = connection.execute("""
            SELECT DISTINCT OWNER
            FROM ALL_TAB_COLUMNS
            ORDER BY OWNER
        """)
        return [row[0] for row in cursor]

    def has_table(self, connection, table_name, schema=None, **kw):
        """检查表是否存在"""
        schema = schema or self.default_schema_name
        cursor = connection.execute("""
            SELECT TABLE_NAME
            FROM ALL_TABLES
            WHERE OWNER = :schema
            AND TABLE_NAME = :table_name
        """, {'schema': schema.upper(), 'table_name': table_name.upper()})
        return cursor.fetchone() is not None

    def get_table_names(self, connection, schema=None, **kw):
        """获取所有表名"""
        schema = schema or self.default_schema_name
        cursor = connection.execute("""
            SELECT TABLE_NAME
            FROM ALL_TABLES
            WHERE OWNER = :schema
            ORDER BY TABLE_NAME
        """, {'schema': schema.upper()})
        return [row[0] for row in cursor]

    def get_view_names(self, connection, schema=None, **kw):
        """获取所有视图名"""
        schema = schema or self.default_schema_name
        cursor = connection.execute("""
            SELECT VIEW_NAME
            FROM ALL_VIEWS
            WHERE OWNER = :schema
            ORDER BY VIEW_NAME
        """, {'schema': schema.upper()})
        return [row[0] for row in cursor]

    def get_columns(self, connection, table_name, schema=None, **kw):
        """获取表的所有列信息"""
        schema = schema or self.default_schema_name
        cursor = connection.execute("""
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                DATA_LENGTH,
                DATA_PRECISION,
                DATA_SCALE,
                NULLABLE
            FROM ALL_TAB_COLUMNS
            WHERE OWNER = :schema
            AND TABLE_NAME = :table_name
            ORDER BY COLUMN_ID
        """, {'schema': schema.upper(), 'table_name': table_name.upper()})

        columns = []
        for row in cursor:
            col_name, data_type, data_length, data_precision, data_scale, nullable = row

            # 构造列定义
            col_def = {
                'name': col_name.lower(),
                'type': self._get_column_type(data_type, data_precision, data_scale, data_length),
                'nullable': nullable == 'Y',
                'default': None
            }
            columns.append(col_def)

        return columns

    def _get_column_type(self, type_name, precision, scale, length):
        """将达梦类型转换为 SQLAlchemy 类型"""
        type_name = type_name.upper()

        type_map = {
            'VARCHAR': sqltypes.VARCHAR,
            'VARCHAR2': sqltypes.VARCHAR,
            'CHAR': sqltypes.CHAR,
            'NCHAR': sqltypes.NCHAR,
            'NVARCHAR': sqltypes.NVARCHAR,
            'NVARCHAR2': sqltypes.NVARCHAR,
            'TEXT': sqltypes.TEXT,
            'CLOB': sqltypes.TEXT,
            'NCLOB': sqltypes.TEXT,
            'BLOB': sqltypes.BLOB,
            'BINARY': sqltypes.BINARY,
            'VARBINARY': sqltypes.VARBINARY,
            'NUMBER': sqltypes.NUMERIC,
            'NUMERIC': sqltypes.NUMERIC,
            'DECIMAL': sqltypes.DECIMAL,
            'INTEGER': sqltypes.INTEGER,
            'INT': sqltypes.INTEGER,
            'BIGINT': sqltypes.BIGINT,
            'SMALLINT': sqltypes.SMALLINT,
            'TINYINT': sqltypes.SMALLINT,
            'FLOAT': sqltypes.FLOAT,
            'DOUBLE': sqltypes.FLOAT,
            'REAL': sqltypes.REAL,
            'DATE': sqltypes.DATE,
            'TIME': sqltypes.TIME,
            'TIMESTAMP': sqltypes.TIMESTAMP,
            'DATETIME': sqltypes.DATETIME,
            'BIT': sqltypes.BOOLEAN,
            'BOOLEAN': sqltypes.BOOLEAN,
        }

        type_class = type_map.get(type_name, sqltypes.String)

        # 根据类型添加长度或精度参数
        if type_name in ('VARCHAR', 'VARCHAR2', 'CHAR', 'NCHAR', 'NVARCHAR', 'NVARCHAR2'):
            if length:
                return type_class(length=length)
        elif type_name in ('NUMBER', 'NUMERIC', 'DECIMAL'):
            if precision and scale:
                return type_class(precision=precision, scale=scale)
            elif precision:
                return type_class(precision=precision)

        return type_class()


# 注册达梦方言到 SQLAlchemy
from sqlalchemy.dialects import registry
registry.register("dm.dmPython", "utils.dm_dialect", "DMDialect")
registry.register("dm", "utils.dm_dialect", "DMDialect")
