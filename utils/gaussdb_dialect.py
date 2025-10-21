"""
自定义 GaussDB SQLAlchemy 方言
解决 openGauss 版本字符串解析问题
"""
import re
from sqlalchemy.dialects.postgresql.psycopg import PGDialect_psycopg
from sqlalchemy import __version__ as sa_version


class GaussDBDialect(PGDialect_psycopg):
    """
    GaussDB 自定义方言,继承自 PostgreSQL psycopg 方言
    主要解决版本号解析问题
    """
    name = 'gaussdb'
    driver = 'psycopg'

    def _get_server_version_info(self, connection):
        """
        重写版本信息获取方法,处理 openGauss 特殊的版本字符串格式

        openGauss 版本格式示例:
        (openGauss 7.0.0-RC1 build 10d38387) compiled at 2025-03-21 18:18:33 ...

        我们需要提取出 7.0.0 部分并转换为元组 (7, 0, 0)
        """
        # 获取原始版本字符串
        v = connection.exec_driver_sql("SELECT version()").scalar()

        # 尝试匹配 openGauss 版本格式
        # 匹配模式: openGauss X.Y.Z 或 openGauss X.Y.Z-RC1
        m = re.match(
            r'.*openGauss\s+(\d+)\.(\d+)\.(\d+)(?:-\w+)?.*',
            v,
            re.IGNORECASE
        )

        if m:
            # 提取版本号的主要部分 (major, minor, patch)
            return tuple(int(x) for x in m.groups())

        # 如果不是 openGauss 格式,尝试标准 PostgreSQL 格式
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
        # 使用 PostgreSQL 10.0 作为基准(GaussDB 兼容 PostgreSQL)
        return (10, 0, 0)


# 注册自定义方言到 SQLAlchemy
from sqlalchemy.dialects import registry
registry.register("gaussdb.psycopg", "utils.gaussdb_dialect", "GaussDBDialect")
