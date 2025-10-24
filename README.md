## rookie_text2data

**Author:** jaguarliuu
**Version:** 1.0.1
**Type:** tool

### Description
A tool that converts natural language into secure and optimized SQL queries, supporting multiple mainstream databases including MySQL, PostgreSQL, Oracle, SQL Server, and Chinese domestic databases (GaussDB, KingbaseES, DM).


### 声明
We are truly grateful for the overwhelming interest in this experimental project. Your feedback is invaluable for improving this plugin. Join our WeChat group for discussions and collaboration opportunities!

> Contact:
>  - Wechat： L1763077056

### ✨ Core Features

#### ​Multi-Database Support
- Native support for 7 database types with automatic syntax adaptation
- International databases: MySQL, PostgreSQL, Oracle, SQL Server
- Chinese domestic databases: GaussDB (Huawei), KingbaseES (KINGBASE), DM (Dameng)
- Automatic SQL syntax adaptation based on database type (e.g., LIMIT vs FETCH FIRST)
- Schema-aware query generation for databases that support schemas

#### ​Security Mechanisms
- Mandatory result set limits (default LIMIT 100, configurable up to 100,000)
- DML operation prohibition (SELECT statements only)
- Field whitelist validation (based on database metadata)
- Least privilege principle for query execution

### Supported Databases
- **MySQL** - Full support with optimized query generation
- **PostgreSQL** - Native support with schema awareness
- **Oracle** - Enterprise database with schema support
- **SQL Server** - Microsoft SQL Server support
- **GaussDB** - Huawei's enterprise-grade database (openGauss compatible)
- **KingbaseES** - Kingbase's PostgreSQL-compatible database
- **DM (Dameng)** - Dameng's Oracle-compatible database

### Supported LLMs
Compatible with ​all non-deep-thinking models
- ChatGLM-6B
- DeepSeek V3
- Qwen-max
...

### Quick Start
#### SQL Generation Component
1. Import the rookie_text2data plugin
2. Configure basic parameters:

| Parameter      | Type           | Required | Description                                                    | Multilingual Support     |
|----------------|----------------|----------|----------------------------------------------------------------|--------------------------|
| db_type        | select         | Yes      | Database type (MySQL/PostgreSQL/Oracle/SQL Server/GaussDB/KingbaseES/DM) | CN/EN/PT    |
| host           | string         | Yes      | Database host/IP address                                       | CN/EN/PT                |
| port           | number         | Yes      | Database port (1-65535)                                        | CN/EN/PT                |
| db_name        | string         | Yes      | Target database name                                           | CN/EN/PT                |
| table_names    | string         | No       | Comma-separated table names (empty for all tables)             | CN (format hints)       |
| schema_name    | string         | No       | Schema name (PostgreSQL default: public, Oracle/DM: uppercase username) | CN/EN/PT    |
| username       | string         | Yes      | Database username                                              | CN/EN/PT                |
| password       | secret-input   | Yes      | Database password                                              | CN/EN/PT                |
| model          | model-selector | Yes      | LLM model configuration                                        | CN/EN/PT                |
| query          | string         | Yes      | Natural language query statement                               | CN/EN/PT                |
| limit          | number         | No       | Query result limit (1-100000, default 100)                     | CN/EN/PT                |
| result_format  | select         | No       | Result format (JSON/TEXT, default JSON)                        | CN/EN/PT                |
| custom_prompt  | string         | No       | Custom prompt for fine-tuning query generation                 | CN/EN/PT                |
| with_comment   | boolean        | No       | Include database comments in schema metadata                   | CN/EN/PT                |

3. Select Model - We recommend using the Qwen-max model. Other models can be tested but deep-thinking models are unsupported.
4. Generate SQL queries using natural language

#### SQL Execution Component
1. Import the rookie_execute_sql plugin
2. Configure basic parameters:

| Parameter      | Type         | Required | Description                                                    | Multilingual Support     |
|----------------|--------------|----------|----------------------------------------------------------------|--------------------------|
| db_type        | select       | Yes      | Database type (MySQL/PostgreSQL/Oracle/SQL Server/GaussDB/KingbaseES/DM) | CN/EN/PT    |
| host           | string       | Yes      | Database host/IP address                                       | CN/EN/PT                |
| port           | number       | Yes      | Database port (1-65535)                                        | CN/EN/PT                |
| db_name        | string       | Yes      | Target database name                                           | CN/EN/PT                |
| username       | string       | Yes      | Database username                                              | CN/EN/PT                |
| password       | secret-input | Yes      | Database password                                              | CN/EN/PT                |
| schema         | string       | No       | Schema name (PostgreSQL default: public, Oracle/DM: uppercase username) | CN/EN/PT    |
| sql            | string       | Yes      | SQL query to execute                                           | CN/EN/PT                |
| result_format  | select       | No       | Result format (JSON/TEXT/CSV, default JSON)                    | CN/EN/PT                |

3. Click "Execute" to run the SQL statement

### Database-Specific Notes

#### Chinese Domestic Databases
- **GaussDB**: Compatible with PostgreSQL protocol, uses SCRAM-SHA-256 authentication
- **KingbaseES**: PostgreSQL-compatible, supports schema-based organization
- **DM (Dameng)**: Oracle-compatible, uses Oracle-style schema management

#### Schema Configuration
- **PostgreSQL/GaussDB/KingbaseES**: Default schema is `public`, can be customized
- **Oracle/DM**: Default schema is the uppercase version of your username (e.g., user `admin` → schema `ADMIN`)
- **MySQL/SQL Server**: Schema parameter not required

### License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.