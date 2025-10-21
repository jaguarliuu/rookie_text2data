from typing import Any, Dict, Optional, Union
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus # 用于对URL进行编码
import atexit
import logging
import time

# 导入 GaussDB 自定义方言以注册到 SQLAlchemy
try:
    from .gaussdb_dialect import GaussDBDialect
except ImportError:
    pass  # 如果导入失败,使用标准 PostgreSQL 方言

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_connection')

# 全局引擎缓存，用于存储和复用数据库连接
_ENGINE_CACHE: Dict[str, Any] = {}
# 连接计数器，用于跟踪活跃连接
_CONNECTION_COUNTERS: Dict[str, int] = {}
# 引擎创建时间，用于跟踪引擎的生命周期
_ENGINE_CREATION_TIME: Dict[str, float] = {}

def format_schema_dsl(schema: dict[str, Any], with_type: bool = True, with_comment: bool = False) -> str:
    """
    将数据库表结构压缩为DSL格式
    :param schema: get_db_schema 返回的结构
    :param with_type: 是否保留字段类型
    :param with_comment: 是否保留字段注释
    :return: 压缩后的 DSL 字符串
    """
    type_aliases = {
        'INTEGER': 'i', 'INT': 'i', 'BIGINT': 'i', 'SMALLINT': 'i', 'TINYINT': 'i',
        'VARCHAR': 's', 'TEXT': 's', 'CHAR': 's',
        'DATETIME': 'dt', 'TIMESTAMP': 'dt', 'DATE': 'dt',
        'DECIMAL': 'f', 'NUMERIC': 'f', 'FLOAT': 'f', 'DOUBLE': 'f',
        'BOOLEAN': 'b', 'BOOL': 'b',
        'JSON': 'j'
    }
    lines = []
    for table_name, table_data in schema.items():
        column_parts = []

        for col in table_data['columns']:
            parts = [col['name']]
            if with_type:
                raw_type = col['type'].split('(')[0].upper()
                col_type = type_aliases.get(raw_type, raw_type.lower())
                parts.append(col_type)
            if with_comment and col.get('comment'):
                parts.append(f"# {col['comment']}")
            column_parts.append(":".join(parts))

        # 构建表注释
        if with_comment and table_data.get('comment'):
            lines.append(f"# {table_data['comment']}")
        lines.append(f"T:{table_name}({', '.join(column_parts)})")

    return "\n".join(lines)

def get_engine_key(
    db_type: str,
    host: str,
    port: int,
    database: str,
    username: str,
    schema: Optional[str] = None
) -> str:
    """
    生成用于缓存引擎的唯一键
    """
    schema_part = f"/{schema}" if schema else ""
    return f"{db_type}://{username}@{host}:{port}/{database}{schema_part}"

def get_or_create_engine(
    db_type: str,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    schema: Optional[str] = None
) -> Any:
    """
    获取或创建数据库引擎实例
    """
    # 生成引擎缓存键
    engine_key = get_engine_key(db_type, host, port, database, username, schema)
    
    # 检查缓存中是否已存在引擎实例
    if engine_key in _ENGINE_CACHE:
        logger.info(f"复用已有引擎: {engine_key} (创建于 {time.time() - _ENGINE_CREATION_TIME[engine_key]:.2f} 秒前)")
        return _ENGINE_CACHE[engine_key]
    
    # 参数预处理
    driver = _get_driver(db_type)
    encoded_username = quote_plus(username)
    encoded_password = quote_plus(password)
    connect_args = {}

    # PostgreSQL 和 GaussDB schema 特殊处理
    if db_type.lower() in ('postgresql', 'gaussdb') and schema:
        connect_args['options'] = f"-c search_path={schema}"

    # 构建连接字符串
    connection_uri = _build_connection_uri(
        db_type, driver, encoded_username, encoded_password,
        host, port, database
    )
    
    # 创建数据库引擎
    logger.info(f"创建新引擎: {engine_key}")
    engine = create_engine(
        connection_uri, 
        connect_args=connect_args,
        # 添加连接池配置，便于监控
        pool_pre_ping=True,  # 在使用连接前检查其有效性
        pool_recycle=3600,   # 一小时后回收连接
        echo_pool=True       # 输出连接池事件日志
    )
    
    # 将引擎实例存入缓存
    _ENGINE_CACHE[engine_key] = engine
    _CONNECTION_COUNTERS[engine_key] = 0
    _ENGINE_CREATION_TIME[engine_key] = time.time()
    
    # 记录连接池配置信息
    pool_info = {
        "size": engine.pool.size(),
        "checkedin": engine.pool.checkedin(),
        "overflow": engine.pool.overflow(),
        "checkedout": engine.pool.checkedout()
    }
    logger.info(f"引擎 {engine_key} 连接池初始状态: {pool_info}")
    
    return engine

# 添加连接跟踪函数
def log_connection_status(engine_key: str, action: str):
    """
    记录连接状态变化
    """
    if engine_key not in _ENGINE_CACHE:
        return
    
    engine = _ENGINE_CACHE[engine_key]
    pool_info = {
        "size": engine.pool.size(),
        "checkedin": engine.pool.checkedin(),
        "overflow": engine.pool.overflow(),
        "checkedout": engine.pool.checkedout()
    }
    
    if action == "acquire":
        _CONNECTION_COUNTERS[engine_key] += 1
    elif action == "release":
        _CONNECTION_COUNTERS[engine_key] = max(0, _CONNECTION_COUNTERS[engine_key] - 1)
    
    logger.info(f"{action} 连接 - 引擎: {engine_key}, 活跃连接: {_CONNECTION_COUNTERS[engine_key]}, 连接池状态: {pool_info}")

# 在程序退出时清理所有引擎连接
@atexit.register
def dispose_all_engines():
    """
    在程序退出时关闭所有数据库连接
    """
    logger.info(f"程序退出，开始清理 {len(_ENGINE_CACHE)} 个数据库引擎...")
    
    for key, engine in _ENGINE_CACHE.items():
        # 记录引擎使用情况
        uptime = time.time() - _ENGINE_CREATION_TIME.get(key, time.time())
        active_connections = _CONNECTION_COUNTERS.get(key, 0)
        
        pool_info = {
            "size": engine.pool.size(),
            "checkedin": engine.pool.checkedin(),
            "overflow": engine.pool.overflow(),
            "checkedout": engine.pool.checkedout()
        }
        
        logger.info(f"释放引擎: {key}, 运行时间: {uptime:.2f}秒, 活跃连接: {active_connections}, 连接池状态: {pool_info}")
        engine.dispose()
        logger.info(f"引擎 {key} 已释放")
    
    _ENGINE_CACHE.clear()
    _CONNECTION_COUNTERS.clear()
    _ENGINE_CREATION_TIME.clear()
    logger.info("所有数据库引擎已清理完毕")

def execute_sql(
    db_type: str,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    sql: str,
    params: Optional[dict[str, Any]] = None,
    schema: Optional[str] = None
) -> Union[list[dict[str, Any]], dict[str, Any], None]:
    """
    增强版 SQL 执行函数，支持 PostgreSQL schema
    
    参数新增:
        schema: 指定目标schema（主要用于PostgreSQL）
    """
    start_time = time.time()
    # 参数预处理
    params = params or {}
    
    # 获取引擎键，用于日志记录
    engine_key = get_engine_key(db_type, host, port, database, username, schema)
    
    # 获取或创建数据库引擎
    engine = get_or_create_engine(
        db_type, host, port, database, username, password, schema
    )

    # 记录SQL执行开始
    truncated_sql = sql[:100] + "..." if len(sql) > 100 else sql
    logger.info(f"开始执行SQL - 引擎: {engine_key}, SQL: {truncated_sql}")
    
    try:
        # 记录连接获取
        log_connection_status(engine_key, "acquire")
        
        with engine.begin() as conn:
            # 显式设置schema（部分数据库需要）
            if db_type.lower() in ('postgresql', 'gaussdb') and schema:
                conn.execute(text(f"SET search_path TO {schema}"))
            elif db_type.lower() in ('oracle', 'dm') and schema:
                # Oracle 和达梦数据库使用 ALTER SESSION 设置当前 schema
                conn.execute(text(f"ALTER SESSION SET CURRENT_SCHEMA = {schema}"))

            result_proxy = conn.execute(text(sql), params)
            result = _process_result(result_proxy)
            
            # 记录SQL执行结束
            execution_time = time.time() - start_time
            result_size = len(result) if isinstance(result, list) else 1 if result else 0
            logger.info(f"SQL执行完成 - 引擎: {engine_key}, 耗时: {execution_time:.3f}秒, 结果行数: {result_size}")
            
            return result
            
    except SQLAlchemyError as e:
        error_msg = str(e)
        logger.error(f"SQL执行失败 - 引擎: {engine_key}, 错误: {error_msg}")
        raise ValueError(f"数据库操作失败：{error_msg}")
    finally:
        # 记录连接释放
        log_connection_status(engine_key, "release")

def _get_driver(db_type: str) -> str:
    """获取数据库驱动"""
    drivers = {
        'mysql': 'pymysql',
        'oracle': 'oracledb',  # 使用新的 python-oracledb 驱动
        'sqlserver': 'pymssql',
        'postgresql': 'psycopg2',
        'gaussdb': 'psycopg',  # 仅 GaussDB 使用 psycopg3，避免版本解析问题
        'dm': 'oracledb'  # 达梦数据库使用 oracledb 驱动（兼容 Oracle 协议）
    }
    return drivers.get(db_type.lower(), '')

def _build_connection_uri(
    db_type: str,
    driver: str,
    username: str,
    password: str,
    host: str,
    port: int,
    database: str,
) -> str:
    """构建数据库连接字符串"""

    # 处理特殊数据库类型
    if db_type == 'sqlserver':
        db_type = 'mssql'
    elif db_type == 'gaussdb':
        # GaussDB 使用自定义方言来处理版本解析问题
        # 只禁用 SSL，保留 SCRAM-SHA-256 等认证方式的支持
        return f"gaussdb+{driver}://{username}:{password}@{host}:{port}/{database}?sslmode=disable"
    elif db_type == 'dm':
        # 达梦数据库使用 Oracle 驱动（兼容 Oracle 协议）
        # 格式：oracle+oracledb://user:pass@host:port/?service_name=SYSDBA
        return f"oracle+{driver}://{username}:{password}@{host}:{port}/?service_name=SYSDBA"

    return f"{db_type}+{driver}://{username}:{password}@{host}:{port}/{database}"


def _process_result(result_proxy) -> Union[list[dict], dict, None]:
    """处理执行结果"""
    if result_proxy.returns_rows:
        return [dict(row._mapping) for row in result_proxy]
    return {"rowcount": result_proxy.rowcount}