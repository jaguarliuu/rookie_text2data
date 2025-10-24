## rookie_text2data

**Author:** jaguarliuu
**Version:** 1.0.1
**Type:** tool

### Description
将自然语言转换为安全、优化的 SQL 查询工具，支持多种主流数据库，包括 MySQL、PostgreSQL、Oracle、SQL Server 以及国产数据库（高斯、人大金仓、达梦）。


### 声明
承蒙厚爱，没有想到一个偶然的想法和基础实践受到这么多人的关注，在此表示感谢！
会积极完善插件，欢迎大家提出宝贵意见！

为方便交流，搞个交流群，大家一起交流学习！


> Contact:
>  - Wechat： L1763077056

### ✨ 核心特性

#### ​**多数据库支持**
- 原生支持 7 种数据库类型，自动语法适配
- 国际主流数据库：MySQL、PostgreSQL、Oracle、SQL Server
- 国产数据库：GaussDB（华为高斯）、KingbaseES（人大金仓）、DM（达梦）
- 自动识别数据库类型生成适配的 SQL 语法（如 `LIMIT` vs `FETCH FIRST`）
- 支持 Schema 感知的查询生成

#### ​**安全防护**
- 强制结果集限制（默认 `LIMIT 100`，可配置至 100,000）
- 禁止 DML 操作（仅允许 SELECT 语句）
- 字段白名单验证（基于数据库元数据）
- 使用最小权限原则执行查询

### 数据库支持
- **MySQL** - 完整支持，优化查询生成
- **PostgreSQL** - 原生支持，Schema 感知
- **Oracle** - 企业级数据库，支持 Schema
- **SQL Server** - 微软 SQL Server 支持
- **GaussDB** - 华为企业级数据库（兼容 openGauss）
- **KingbaseES** - 人大金仓数据库（兼容 PostgreSQL）
- **DM（达梦）** - 达梦数据库（兼容 Oracle）

### 大模型支持

> 理论上，支持所有**非深度思考**大模型

- ChatGLM-6B
- DeepSeek V3
- Qwen-max
- ...

### 快速开始
#### SQL生成组件
1. 引入 rookie_text2data 插件
2. 完成基础参数配置

| 参数名         | 类型           | 必填 | 描述                                                        | 多语言支持     |
|----------------|----------------|------|-------------------------------------------------------------|----------------|
| db_type        | select         | 是   | 数据库类型（MySQL/PostgreSQL/Oracle/SQL Server/GaussDB/KingbaseES/DM） | 中/英/葡 |
| host           | string         | 是   | 数据库主机地址                                              | 中/英/葡       |
| port           | number         | 是   | 数据库端口（1-65535）                                       | 中/英/葡       |
| db_name        | string         | 是   | 目标数据库名称                                              | 中/英/葡       |
| table_names    | string         | 否   | 多表逗号分隔（空则全库）                                    | 中文含格式说明 |
| schema_name    | string         | 否   | Schema名称（PostgreSQL默认为public，Oracle/DM默认为用户名大写） | 中/英/葡   |
| username       | string         | 是   | 数据库用户名                                                | 中/英/葡       |
| password       | secret-input   | 是   | 数据库密码                                                  | 中/英/葡       |
| model          | model-selector | 是   | LLM 模型配置                                                | 中/英/葡       |
| query          | string         | 是   | 自然语言查询语句                                            | 中/英/葡       |
| limit          | number         | 否   | 查询结果限制（1-100000，默认100）                           | 中/英/葡       |
| result_format  | select         | 否   | 结果格式（JSON/TEXT，默认JSON）                             | 中/英/葡       |
| custom_prompt  | string         | 否   | 自定义提示词，用于微调查询生成                              | 中/英/葡       |
| with_comment   | boolean        | 否   | 在Schema元数据中包含数据库注释                              | 中/英/葡       |

3. 选择模型 - 推荐使用 `Qwen-max` 模型，其他模型请自行尝试。不支持深度思考模型。
4. 使用自然语言生成 SQL 查询语句

#### SQL执行组件
1. 引入 rookie_excute_sql 插件
2. 完成基础参数配置

| 参数名         | 类型         | 必填 | 描述                                                        | 多语言支持     |
|----------------|--------------|------|-------------------------------------------------------------|----------------|
| db_type        | select       | 是   | 数据库类型（MySQL/PostgreSQL/Oracle/SQL Server/GaussDB/KingbaseES/DM） | 中/英/葡 |
| host           | string       | 是   | 数据库主机地址                                              | 中/英/葡       |
| port           | number       | 是   | 数据库端口（1-65535）                                       | 中/英/葡       |
| db_name        | string       | 是   | 目标数据库名称                                              | 中/英/葡       |
| username       | string       | 是   | 数据库用户名                                                | 中/英/葡       |
| password       | secret-input | 是   | 数据库密码                                                  | 中/英/葡       |
| schema         | string       | 否   | Schema名称（PostgreSQL默认为public，Oracle/DM默认为用户名大写） | 中/英/葡   |
| sql            | string       | 是   | 待执行的 SQL 语句                                           | 中/英/葡       |
| result_format  | select       | 否   | 结果格式（JSON/TEXT/CSV，默认JSON）                         | 中/英/葡       |

3. 点击执行，执行 SQL 语句

### 数据库特定说明

#### 国产数据库支持
- **GaussDB（高斯数据库）**：兼容 PostgreSQL 协议，使用 SCRAM-SHA-256 认证
- **KingbaseES（人大金仓）**：兼容 PostgreSQL，支持基于 Schema 的组织方式
- **DM（达梦数据库）**：兼容 Oracle，使用 Oracle 风格的 Schema 管理

#### Schema 配置说明
- **PostgreSQL/GaussDB/KingbaseES**：默认 Schema 为 `public`，可自定义
- **Oracle/DM**：默认 Schema 为用户名的大写形式（例如：用户 `admin` → Schema `ADMIN`）
- **MySQL/SQL Server**：不需要配置 Schema 参数

#### 驱动依赖说明
- **达梦数据库（DM）**：需要从达梦官方获取 dmPython 驱动并手动安装
- **其他数据库**：所需驱动已在 requirements.txt 中配置，pip install 即可

### 许可证

本项目采用 Apache License 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详细信息。