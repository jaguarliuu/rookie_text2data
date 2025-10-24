"""
自定义 KingbaseES SQLAlchemy 方言
解决人大金仓数据库版本字符串解析问题
"""
import re
from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2


class KingbaseESDialect(PGDialect_psycopg2):
    """
    KingbaseES 自定义方言,继承自 PostgreSQL psycopg2 方言
    主要解决版本号解析问题

    KingbaseES 是人大金仓开发的国产数据库,兼容 PostgreSQL 协议
    """
    name = 'kingbase'
    driver = 'psycopg2'

    def _get_server_version_info(self, connection):
        """
        重写版本信息获取方法,处理 KingbaseES 特殊的版本字符串格式

        KingbaseES 版本格式示例:
        Kingbase V008R006C008B0014 on x86_64-pc-linux-gnu, compiled by gcc...
        或
        KingbaseES V8R6 compiled at 2023-01-01 00:00:00

        我们需要提取出版本号并转换为元组,例如 (8, 6, 0)
        """
        # 获取原始版本字符串
        v = connection.exec_driver_sql("SELECT version()").scalar()

        # 尝试匹配 KingbaseES 版本格式 V008R006C008 或 V8R6
        # 匹配模式: V008R006 或 V8R6
        m = re.match(
            r'.*[Kk]ingbase(?:ES)?\s+V0*(\d+)R0*(\d+)(?:C0*(\d+))?.*',
            v,
            re.IGNORECASE
        )

        if m:
            # 提取版本号的主要部分 (major, minor, patch)
            major, minor, patch = m.groups()
            return (
                int(major),
                int(minor),
                int(patch) if patch else 0
            )

        # 如果不是 KingbaseES 格式,尝试标准 PostgreSQL 格式
        # 格式: PostgreSQL X.Y.Z
        m = re.match(
            r'.*PostgreSQL\s+(\d+)\.(\d+)(?:\.(\d+))?.*',
            v,
            re.IGNORECASE
        )

        if m:
            major, minor, patch = m.groups()
            # patch 可能不存在(PostgreSQL 10+ 只有 major.minor)
            return (int(major), int(minor), int(patch) if patch else 0)

        # 如果都不匹配,返回一个安全的默认版本号
        # 使用 PostgreSQL 10.0 作为基准(KingbaseES 兼容 PostgreSQL)
        return (10, 0, 0)


# 注册自定义方言到 SQLAlchemy
from sqlalchemy.dialects import registry
registry.register("kingbase.psycopg2", "utils.kingbase_dialect", "KingbaseESDialect")
registry.register("kingbase", "utils.kingbase_dialect", "KingbaseESDialect")
