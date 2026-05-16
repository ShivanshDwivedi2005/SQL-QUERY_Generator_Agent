"""
Core tools for Neon/PostgreSQL database interaction and SQL operations.
These tools are used by the agent to explore schema, validate queries, and
execute read-only SQL.
"""
import time
import csv
import io
import re
from decimal import Decimal
from datetime import date, datetime, time as dt_time
from typing import Any, Dict, List, Optional, Tuple

import psycopg
import sqlparse
from psycopg import sql as pg_sql
from psycopg.rows import dict_row

from config import BLOCKED_KEYWORDS, DATABASE_URL, DEFAULT_LIMIT, MAX_QUERY_TIMEOUT


class DatabaseTools:
    """Tools for safe PostgreSQL interaction."""

    def __init__(self, db_url: str = None):
        """Initialize database connection."""
        self.db_url = db_url or DATABASE_URL
        self.connection = None
        self.available = False
        self.database_name = "Neon PostgreSQL"
        self.connection_error = None
        self._connect()

    def _connect(self):
        """Create a Neon/PostgreSQL connection."""
        if not self.db_url:
            self.available = False
            return

        try:
            self.connection = psycopg.connect(
                self.db_url,
                connect_timeout=MAX_QUERY_TIMEOUT,
                row_factory=dict_row,
            )
            self.connection.autocommit = True

            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT set_config('statement_timeout', %s, false)",
                    (str(MAX_QUERY_TIMEOUT * 1000),),
                )
                cursor.execute("SELECT current_database() AS database_name")
                row = cursor.fetchone()
                if row and row.get("database_name"):
                    self.database_name = row["database_name"]

            self.available = True
        except Exception as e:
            self.available = False
            self.connection = None
            self.connection_error = str(e)

    def ensure_connected(self) -> bool:
        """Verify the connection is alive; reconnect if it dropped."""
        if not self.db_url:
            self.available = False
            return False

        if self.available and self.connection is not None:
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return True
            except Exception as e:
                self.available = False
                self.connection_error = str(e)
                try:
                    self.connection.close()
                except Exception:
                    pass
                self.connection = None

        self._connect()
        return self.available

    def _public_table_names(self) -> List[str]:
        """Return non-system table names in public schemas."""
        if not self.available:
            return []

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                  AND table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name
                """
            )
            rows = cursor.fetchall()

        names = []
        for row in rows:
            schema = row["table_schema"]
            table = row["table_name"]
            names.append(table if schema == "public" else f"{schema}.{table}")
        return names

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        """Quote a PostgreSQL identifier or schema-qualified identifier."""
        parts = [part.strip() for part in identifier.split(".") if part.strip()]
        return ".".join(f'"{part.replace(chr(34), chr(34) + chr(34))}"' for part in parts)

    @staticmethod
    def _split_table_name(table_name: str) -> Tuple[str, str]:
        parts = [part.strip().strip('"') for part in table_name.split(".") if part.strip()]
        if len(parts) == 1:
            return "public", parts[0]
        return parts[-2], parts[-1]

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Convert database values into JSON-serializable values."""
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date, dt_time)):
            return value.isoformat()
        return value

    def _serialize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {key: self._serialize_value(value) for key, value in row.items()}

    @staticmethod
    def _safe_identifier(value: str, fallback: str) -> str:
        """Convert arbitrary text into a safe PostgreSQL identifier."""
        identifier = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
        identifier = re.sub(r"_+", "_", identifier).strip("_")
        if not identifier:
            identifier = fallback
        if identifier[0].isdigit():
            identifier = f"{fallback}_{identifier}"
        return identifier[:60]

    def _table_exists(self, table_name: str, schema_name: str = "public") -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = %s
                      AND table_name = %s
                ) AS exists
                """,
                (schema_name, table_name),
            )
            return bool(cursor.fetchone()["exists"])

    def _unique_table_name(self, base_name: str) -> str:
        """Find a non-conflicting table name in the public schema."""
        table_name = base_name
        suffix = 2
        while self._table_exists(table_name):
            trimmed_base = base_name[:55]
            table_name = f"{trimmed_base}_{suffix}"
            suffix += 1
        return table_name

    @staticmethod
    def _deduplicate_columns(columns: List[str]) -> List[str]:
        """Ensure uploaded CSV column names are valid and unique."""
        seen = {}
        result = []
        for index, column in enumerate(columns, 1):
            base = DatabaseTools._safe_identifier(column or f"column_{index}", f"column_{index}")
            count = seen.get(base, 0)
            seen[base] = count + 1
            result.append(base if count == 0 else f"{base}_{count + 1}")
        return result

    def upload_csv_data(self, filename: str, content: bytes) -> Dict[str, Any]:
        """
        Create a new PostgreSQL table from uploaded CSV data.
        All uploaded columns are stored as TEXT to avoid lossy type inference.
        """
        if not self.available:
            return {"success": False, "error": "Database not available"}

        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return {"success": False, "error": "CSV file must be UTF-8 encoded"}

        try:
            reader = csv.reader(io.StringIO(decoded))
            rows = list(reader)
        except csv.Error as e:
            return {"success": False, "error": f"Invalid CSV file: {str(e)}"}

        if not rows:
            return {"success": False, "error": "CSV file is empty"}

        raw_headers = rows[0]
        if not raw_headers or all(not header.strip() for header in raw_headers):
            return {"success": False, "error": "CSV file must include a header row"}

        columns = self._deduplicate_columns(raw_headers)
        data_rows = rows[1:]
        normalized_rows = []
        for row in data_rows:
            if len(row) < len(columns):
                row = row + [""] * (len(columns) - len(row))
            elif len(row) > len(columns):
                row = row[:len(columns)]
            normalized_rows.append([value if value != "" else None for value in row])

        table_base = self._safe_identifier(filename.rsplit(".", 1)[0], "uploaded_data")
        table_name = self._unique_table_name(table_base)

        create_columns = [
            pg_sql.SQL("{} TEXT").format(pg_sql.Identifier(column))
            for column in columns
        ]
        create_query = pg_sql.SQL("CREATE TABLE {} ({})").format(
            pg_sql.Identifier(table_name),
            pg_sql.SQL(", ").join(create_columns),
        )

        insert_query = pg_sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            pg_sql.Identifier(table_name),
            pg_sql.SQL(", ").join(pg_sql.Identifier(column) for column in columns),
            pg_sql.SQL(", ").join(pg_sql.Placeholder() for _ in columns),
        )

        try:
            with self.connection.transaction():
                with self.connection.cursor() as cursor:
                    cursor.execute(create_query)
                    if normalized_rows:
                        cursor.executemany(insert_query, normalized_rows)
        except Exception as e:
            return {"success": False, "error": f"Failed to import CSV: {str(e)}"}

        return {
            "success": True,
            "table": table_name,
            "columns": columns,
            "rows_inserted": len(normalized_rows),
            "message": f"Uploaded {len(normalized_rows)} row(s) into table '{table_name}'",
        }

    def get_schema_info(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get schema information for tables.

        Args:
            table_name: Specific table name, or None for all tables

        Returns:
            Dictionary with schema information
        """
        if not self.available:
            return {"error": "Database not available"}

        try:
            if table_name is None:
                tables = self._public_table_names()
                return {
                    "type": "all_tables",
                    "tables": tables,
                    "count": len(tables),
                    "dialect": "postgresql",
                }

            schema_name, plain_table_name = self._split_table_name(table_name)
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s
                      AND table_name = %s
                    ORDER BY ordinal_position
                    """,
                    (schema_name, plain_table_name),
                )
                column_rows = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                      AND tc.table_schema = %s
                      AND tc.table_name = %s
                    """,
                    (schema_name, plain_table_name),
                )
                primary_keys = {row["column_name"] for row in cursor.fetchall()}

                cursor.execute(
                    """
                    SELECT
                        kcu.column_name,
                        ccu.table_schema AS references_schema,
                        ccu.table_name AS references_table,
                        ccu.column_name AS references_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu
                      ON ccu.constraint_name = tc.constraint_name
                     AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_schema = %s
                      AND tc.table_name = %s
                    """,
                    (schema_name, plain_table_name),
                )
                foreign_key_rows = cursor.fetchall()

            if not column_rows:
                return {"error": f"Table '{table_name}' not found"}

            columns = [
                {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "primary_key": row["column_name"] in primary_keys,
                    "default_value": row["column_default"],
                }
                for row in column_rows
            ]

            foreign_keys = [
                {
                    "column": row["column_name"],
                    "references_table": (
                        row["references_table"]
                        if row["references_schema"] == "public"
                        else f'{row["references_schema"]}.{row["references_table"]}'
                    ),
                    "references_column": row["references_column"],
                }
                for row in foreign_key_rows
            ]

            return {
                "type": "table_schema",
                "table_name": table_name,
                "columns": columns,
                "foreign_keys": foreign_keys,
                "dialect": "postgresql",
            }
        except Exception as e:
            return {"error": f"Error reading schema: {str(e)}"}

    def explore_data(
        self,
        table_name: str,
        column_name: Optional[str] = None,
        sample_size: int = 5,
    ) -> Dict[str, Any]:
        """
        Explore data in a table or column.
        """
        if not self.available:
            return {"error": "Database not available"}

        try:
            safe_table = self._quote_identifier(table_name)
            sample_size = max(1, min(int(sample_size or 5), DEFAULT_LIMIT))

            with self.connection.cursor() as cursor:
                if column_name is None:
                    cursor.execute(f"SELECT * FROM {safe_table} LIMIT %s", (sample_size,))
                    rows = cursor.fetchall()
                    columns = [desc.name for desc in cursor.description]

                    return {
                        "type": "sample_rows",
                        "table": table_name,
                        "columns": columns,
                        "sample_data": [self._serialize_row(row) for row in rows],
                        "sample_size": len(rows),
                    }

                safe_column = self._quote_identifier(column_name)
                cursor.execute(
                    f"""
                    SELECT
                        COUNT(DISTINCT {safe_column}) AS distinct_count,
                        COUNT({safe_column}) AS non_null_count,
                        COUNT(*) AS total_count
                    FROM {safe_table}
                    """
                )
                stats = cursor.fetchone()

                cursor.execute(
                    f"""
                    SELECT DISTINCT {safe_column} AS value
                    FROM {safe_table}
                    WHERE {safe_column} IS NOT NULL
                    LIMIT %s
                    """,
                    (sample_size,),
                )
                sample_values = [
                    self._serialize_value(row["value"]) for row in cursor.fetchall()
                ]

            return {
                "type": "column_stats",
                "table": table_name,
                "column": column_name,
                "distinct_count": stats["distinct_count"],
                "non_null_count": stats["non_null_count"],
                "total_count": stats["total_count"],
                "sample_values": sample_values,
            }
        except Exception as e:
            return {"error": f"Error exploring data: {str(e)}"}

    def get_table_stats(self) -> Dict[str, Any]:
        """Get row counts for all user tables."""
        if not self.available:
            return {"error": "Database not available"}

        try:
            stats = {}
            for table in self._public_table_names():
                safe_table = self._quote_identifier(table)
                with self.connection.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) AS row_count FROM {safe_table}")
                    count = cursor.fetchone()["row_count"]
                stats[table] = {"row_count": count}

            return {
                "type": "table_stats",
                "tables": stats,
                "dialect": "postgresql",
            }
        except Exception as e:
            return {"error": f"Error reading table stats: {str(e)}"}

    def validate_sql(self, sql: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate SQL query for safety and best practices.
        """
        sql_upper = sql.upper().strip()

        if ";" in sql.rstrip(";"):
            return False, "Blocked operation: multiple SQL statements are not allowed.", None

        for keyword in BLOCKED_KEYWORDS:
            if keyword in sql_upper:
                return False, f"Blocked operation: {keyword}. Only read-only queries allowed.", None

        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            return False, "Only SELECT queries are allowed.", None

        parsed = sqlparse.parse(sql)
        if not parsed:
            return False, "Invalid SQL syntax.", None

        modified_sql = sql
        if "LIMIT" not in sql_upper:
            if "COUNT(" not in sql_upper and "SUM(" not in sql_upper and "AVG(" not in sql_upper:
                modified_sql = f"{sql.rstrip(';')} LIMIT {DEFAULT_LIMIT}"
                return True, f"Valid. Added LIMIT {DEFAULT_LIMIT} for safety.", modified_sql

        return True, "Valid SQL query.", modified_sql

    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """
        Execute a read-only SQL query and return results.
        """
        if not self.available:
            return {"success": False, "error": "Database not available"}

        cursor = self.connection.cursor()
        start_time = time.time()

        try:
            cursor.execute("BEGIN READ ONLY")
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [desc.name for desc in cursor.description] if cursor.description else []
            cursor.execute("COMMIT")

            execution_time = time.time() - start_time
            results = [self._serialize_row(row) for row in rows]

            return {
                "success": True,
                "sql": sql,
                "columns": columns,
                "results": results,
                "row_count": len(results),
                "execution_time": round(execution_time, 3),
            }
        except Exception as e:
            try:
                cursor.execute("ROLLBACK")
            except Exception:
                pass

            execution_time = time.time() - start_time
            return {
                "success": False,
                "sql": sql,
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time": round(execution_time, 3),
            }
        finally:
            cursor.close()

    def get_database_view(self) -> Dict[str, Any]:
        """Get schema and sample data for all user tables."""
        if not self.available:
            return {"error": "Database not available"}

        tables = []
        stats = self.get_table_stats().get("tables", {})

        for table_name in self._public_table_names():
            schema_info = self.get_schema_info(table_name)
            sample_info = self.explore_data(table_name, sample_size=5)

            columns = [
                {
                    "name": column["name"],
                    "type": column["type"],
                    "notnull": not column["nullable"],
                    "default_value": column.get("default_value"),
                    "pk": column["primary_key"],
                }
                for column in schema_info.get("columns", [])
            ]

            tables.append(
                {
                    "name": table_name,
                    "columns": columns,
                    "row_count": stats.get(table_name, {}).get("row_count", 0),
                    "sample_data": sample_info.get("sample_data", []),
                }
            )

        return {
            "database": self.database_name,
            "dialect": "postgresql",
            "tables": tables,
        }

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def create_tool_functions(db_tools: DatabaseTools):
    """
    Create function definitions for Gemini function calling.

    Returns:
        List of function declarations for Gemini
    """
    return [
        {
            "name": "get_schema_info",
            "description": "Get PostgreSQL schema information. Call with no table_name to list all tables, or with a table_name to get columns, types, and foreign keys.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to get schema for. Leave empty to list all tables.",
                    }
                },
                "required": [],
            },
        },
        {
            "name": "explore_data",
            "description": "Explore data in a PostgreSQL table. Use this to see sample data or check column values before generating SQL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table to explore"},
                    "column_name": {
                        "type": "string",
                        "description": "Specific column to analyze. Leave empty for sample rows.",
                    },
                    "sample_size": {
                        "type": "integer",
                        "description": "Number of samples to return (default 5)",
                    },
                },
                "required": ["table_name"],
            },
        },
        {
            "name": "get_table_stats",
            "description": "Get row counts for all PostgreSQL tables.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "execute_sql",
            "description": "Execute a validated PostgreSQL SELECT query and return results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The PostgreSQL SELECT query to execute",
                    }
                },
                "required": ["sql"],
            },
        },
    ]
