from sqlalchemy.sql import text
from .base import BaseInspector
from sqlalchemy.engine import reflection
from urllib.parse import quote_plus

class OracleInspector(BaseInspector):
    """Oracle元数据获取实现"""
    
    def __init__(self, host: str, port: int, database: str,
                username: str, password: str, schema_name: str = None, **kwargs):
        super().__init__(host, port, database, username, password, schema_name)
        self.schema_name = username.upper()  # Oracle模式名通常与用户名一致[3,8](@ref)
    
    def build_conn_str(self, host: str, port: int, database: str,
                      username: str, password: str) -> str:
        # 使用cx_Oracle驱动，支持SID或Service Name[6,8](@ref)
        return (
            f"oracle+cx_oracle://{quote_plus(username)}:{quote_plus(password)}"
            f"@{host}:{port}/?service_name={database}"
        )
    
    def get_table_names(self, inspector: reflection.Inspector) -> list[str]:
        return inspector.get_table_names(schema=self.schema_name)  # 需指定schema[3](@ref)
    
    def get_table_comment(self, inspector: reflection.Inspector,
                         table_name: str) -> str:
        # 查询ALL_TAB_COMMENTS视图[3,5](@ref)
        with self.engine.connect() as conn:
            sql = text("""
                SELECT COMMENTS 
                FROM ALL_TAB_COMMENTS 
                WHERE OWNER = :owner 
                    AND TABLE_NAME = :table_name
            """)
            return conn.execute(sql, {
                'owner': self.schema_name,
                'table_name': table_name
            }).scalar() or ""
    
    def get_column_comment(self, inspector: reflection.Inspector,
                          table_name: str, column_name: str) -> str:
        # 查询ALL_COL_COMMENTS视图[3](@ref)
        with self.engine.connect() as conn:
            sql = text("""
                SELECT COMMENTS 
                FROM ALL_COL_COMMENTS 
                WHERE OWNER = :owner 
                    AND TABLE_NAME = :table_name 
                    AND COLUMN_NAME = :column_name
            """)
            return conn.execute(sql, {
                'owner': self.schema_name,
                'table_name': table_name,
                'column_name': column_name
            }).scalar() or ""
    
    def normalize_type(self, raw_type: str) -> str:
        # 标准化Oracle类型（如去除精度信息）[3,5](@ref)
        return raw_type.split('(')[0].split('%')[0].upper()