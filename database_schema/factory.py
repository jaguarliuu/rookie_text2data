# database_schema/factory.py
from database_schema.inspectors import (
    MySQLInspector,
    SQLServerInspector,
    PostgreSQLInspector,
    OracleInspector
)

class InspectorFactory:
    @staticmethod
    def create_inspector(db_type: str, **kwargs) -> object:
        """创建数据库检查器实例（绝对路径导入版）"""
        db_type = db_type.lower().strip()
        mapping = {
            'mysql': MySQLInspector,
            'sqlserver': SQLServerInspector,
            'postgresql': PostgreSQLInspector,
            'oracle': OracleInspector
        }
        
        if db_type not in mapping:
            raise ValueError(f"Unsupported database type: {db_type}")
            
        return mapping[db_type](**kwargs)