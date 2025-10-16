# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**rookie_text2data** is a Dify plugin that converts natural language queries into secure, optimized SQL statements. It supports MySQL, PostgreSQL, Oracle, SQL Server, and GaussDB databases with built-in security mechanisms to prevent data leaks and SQL injection.

## Development Commands

### Running the Plugin
```bash
# Start the plugin with extended timeout (120s)
python main.py
```

### Testing
```bash
# Run test file
python _test/test.py

# Test prompt loading
python utils/prompt_loader.py
```

### Dependencies
```bash
# Install dependencies
pip install -r requirements.txt
```

## Architecture Overview

### Core Components

1. **Two-Tool Architecture**
   - `rookie_text2data`: Generates SQL from natural language using LLM
   - `rookie_excute_sql`: Executes generated SQL with security validation

2. **Database Schema Inspection System** (`database_schema/`)
   - **Factory Pattern**: `InspectorFactory` creates database-specific inspectors
   - **Base Inspector**: `BaseInspector` (abstract) defines interface for metadata extraction
   - **Database-Specific Inspectors**: MySQL, PostgreSQL, Oracle, SQL Server, GaussDB implementations
   - **Connector**: `get_db_schema()` orchestrates schema extraction
   - **Formatter**: `format_schema_dsl()` compresses schema into LLM-friendly DSL format

3. **Prompt Template System** (`prompt_templates/sql_generation/`)
   - Jinja2-based templates per database type
   - `PromptLoader` injects database-specific syntax rules
   - Templates enforce security rules (SELECT-only, result limits, field validation)

4. **Database Client** (`utils/alchemy_db_client.py`)
   - SQLAlchemy-based execution with engine caching
   - Connection pooling with lifecycle tracking
   - Automatic cleanup via `atexit` handler

### Security Architecture

The plugin implements defense-in-depth:

- **SQL Generation Phase** (tools/rookie_text2data.py:13-66):
  - Schema whitelist validation via metadata inspection
  - LLM prompt enforces SELECT-only statements
  - Automatic LIMIT clause injection (default: 100 rows)
  - Database-specific syntax validation

- **Execution Phase** (tools/rookie_excute_sql.py:13-201):
  - SQL injection detection via `_contains_risk_commands()` (line 165)
  - Blocks DML operations: DROP, DELETE, TRUNCATE, ALTER, UPDATE, INSERT
  - Parameterized query execution
  - Empty result handling

### Schema DSL Format

The system uses compressed DSL to reduce LLM token usage:

```
T:table_name(field1:i, field2:s, field3:dt)
```

Type abbreviations:
- `i` = INTEGER, INT, BIGINT, SMALLINT, TINYINT
- `s` = VARCHAR, TEXT, CHAR, NVARCHAR, NCHAR
- `dt` = DATETIME, DATE, TIMESTAMP, TIME
- `f` = DECIMAL, NUMERIC, FLOAT, DOUBLE
- `b` = BOOLEAN, BOOL
- `j` = JSON, JSONB

### Database-Specific Handling

Each inspector handles database quirks:

- **MySQL**: Schema equals database name; uses `information_schema.COLUMNS` for comments
- **PostgreSQL**: Supports custom schemas (default: `public`); uses `pg_catalog` for metadata
- **Oracle**: Uses `ROWNUM` for limits; type normalization for Oracle-specific types
- **SQL Server**: Schema defaults to `dbo`; uses `TOP n` syntax
- **GaussDB**: Compatible with PostgreSQL protocol; uses special connection args (`gssencmode=disable`) to bypass SASL authentication; supports both Oracle and PostgreSQL compatibility modes

### Connection Management

The `alchemy_db_client.py` implements:
- **Engine Caching**: Reuses connections via `_ENGINE_CACHE` keyed by `db_type://user@host:port/database/schema`
- **Connection Pooling**: SQLAlchemy pool with pre-ping and 1-hour recycle
- **Lifecycle Tracking**: Logs connection acquire/release, pool status, and uptime
- **Automatic Cleanup**: `dispose_all_engines()` runs at program exit

Key functions:
- `get_or_create_engine()`: Retrieves cached engine or creates new one
- `execute_sql()`: Executes SQL with schema support, logging, and error handling
- `log_connection_status()`: Tracks active connection count and pool state

## Key Implementation Details

### Natural Language → SQL Flow

1. User provides natural language query + database credentials
2. `RookieText2dataTool._invoke()` extracts schema metadata via `get_db_schema()`
3. Schema formatted to DSL via `format_schema_dsl()`
4. `PromptLoader` builds database-specific system prompt
5. LLM generates SQL (model configurable, Qwen-max recommended)
6. SQL returned in JSON or text format

### SQL Execution Flow

1. `RookieExecuteSqlTool._invoke()` validates parameters
2. `_contains_risk_commands()` blocks dangerous operations
3. `execute_sql()` acquires connection from cache/pool
4. For PostgreSQL: sets `search_path` to target schema
5. Executes via SQLAlchemy's `text()` with parameterization
6. Results formatted as JSON/CSV/HTML/text
7. Connection returned to pool

### Prompt Template Customization

Templates located in `prompt_templates/sql_generation/`:
- `base_prompt.jinja`: Common rules for all databases
- `{db_type}_prompt.jinja`: Database-specific overrides

Context variables injected by `PromptLoader.get_prompt()`:
- `db_type`: Database type (MySQL, PostgreSQL, etc.)
- `meta_data`: Compressed DSL schema
- `limit_clause`: Database-specific syntax (LIMIT n, TOP n, ROWNUM <= n, FETCH FIRST n ROWS ONLY)
- `optimization_rules`: Database-specific performance tips
- `user_custom_prompt`: User-provided custom instructions
- `limit`: Maximum result rows (default: 100)

## Common Development Patterns

### Adding a New Database Type

1. Create inspector in `database_schema/inspectors/{dbtype}.py`:
   - Extend `BaseInspector`
   - Implement `build_conn_str()`, `get_table_names()`, `get_table_comment()`, `get_column_comment()`, `normalize_type()`
2. Register in `database_schema/factory.py` mapping
3. Add driver to `requirements.txt` and `_get_driver()` in `alchemy_db_client.py`
4. Create prompt template: `prompt_templates/sql_generation/{dbtype}_prompt.jinja`
5. Update `PromptLoader._get_limit_clause()` and `_get_optimization_rules()`
6. Add to manifest.yaml if needed

### Modifying Security Rules

- SQL injection patterns: Edit `RookieExecuteSqlTool.RISK_KEYWORDS` (line 14)
- Schema validation: Modify `get_db_schema()` in `database_schema/connector.py`
- LLM constraints: Update prompt templates in `prompt_templates/sql_generation/`

### Extending Result Formats

Add format handler in `tools/rookie_excute_sql.py`:
1. Add format to `SUPPORTED_FORMATS` (line 15)
2. Implement `_handle_{format}()` method
3. Update `_handle_result_format()` dispatch logic

## Database Connection Details

### Connection String Formats

Built by `BaseInspector.build_conn_str()` implementations:
- **MySQL**: `mysql+pymysql://{user}:{pass}@{host}:{port}/{db}?charset=utf8mb4`
- **PostgreSQL**: `postgresql+psycopg2://{user}:{pass}@{host}:{port}/{db}`
- **SQL Server**: `mssql+pymssql://{user}:{pass}@{host}:{port}/{db}`
- **Oracle**: `oracle+oracledb://{user}:{pass}@{host}:{port}/{db}` (uses python-oracledb, the modern replacement for cx_Oracle)
- **GaussDB**: `postgresql+psycopg2://{user}:{pass}@{host}:{port}/{db}?sslmode=disable&gssencmode=disable` (uses PostgreSQL protocol with special auth params)

Passwords are URL-encoded via `urllib.parse.quote_plus()`.

### Schema Handling

- **MySQL**: `schema_name` forced to equal `database` (line 13 in mysql.py)
- **PostgreSQL**: Defaults to `public`, customizable via constructor (line 13 in postgresql.py)
- **SQL Server**: Defaults to `dbo` (line 49 in rookie_excute_sql.py)
- **Oracle**: Schema-aware via `schema_name` parameter
- **GaussDB**: Defaults to `public`, same as PostgreSQL (line 13 in gaussdb.py)

## Plugin Metadata

Defined in `manifest.yaml`:
- Entry point: `main.py`
- Python version: 3.12
- Memory limit: 256MB (268435456 bytes)
- Storage: 1MB
- Permissions: tools, LLM models, app integration
- Architectures: amd64, arm64

## Testing Notes

- The `_test/test.py` file contains integration tests
- Prompt templates can be tested via `utils/prompt_loader.py`
- Test different database types by varying `db_type` parameter
- Deep-thinking LLM models are NOT supported (use Qwen-max, DeepSeek V3, ChatGLM-6B, etc.)
