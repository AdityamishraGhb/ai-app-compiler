import logging
import sqlite3
from typing import List

from backend.schemas import DatabaseSchema, DBTable
from backend.schemas.runtime import RuntimeResult

logger = logging.getLogger(__name__)

class RuntimeSimulator:
    """
    Stage 6: Runtime Simulator
    
    Converts a DatabaseSchema into SQLite statements and executes them in an in-memory DB
    to verify execution capability.
    """
    
    def execute(self, db_schema: DatabaseSchema) -> RuntimeResult:
        logger.info("Executing Stage 6: Runtime Simulation")
        statements = self._generate_sql(db_schema)
        
        tables_created = []
        execution_errors = []
        
        # Connect to an in-memory SQLite database
        conn = sqlite3.connect(":memory:")
        # Enable foreign keys in sqlite
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        
        for stmt in statements:
            try:
                cursor.execute(stmt)
                # Try to extract table name if it's a CREATE TABLE statement
                if stmt.strip().upper().startswith("CREATE TABLE"):
                    # Basic extraction: CREATE TABLE [IF NOT EXISTS] tablename
                    parts = stmt.split()
                    if "TABLE" in parts:
                        idx = parts.index("TABLE")
                        # Handle IF NOT EXISTS
                        if len(parts) > idx + 3 and parts[idx+1].upper() == "IF":
                            table_name = parts[idx+4]
                        else:
                            table_name = parts[idx+1]
                        
                        # Remove quotes/brackets if any
                        table_name = table_name.strip("`\"'()").split("(")[0]
                        tables_created.append(table_name)
            except sqlite3.Error as e:
                execution_errors.append(f"SQL Error: {e} \nStatement: {stmt}")
                
        conn.close()
        
        success = len(execution_errors) == 0
        
        return RuntimeResult(
            success=success,
            tables_created=tables_created,
            statements_executed=statements,
            execution_errors=execution_errors
        )

    def _generate_sql(self, db_schema: DatabaseSchema) -> List[str]:
        statements = []
        for table in db_schema.tables:
            stmt = self._generate_create_table(table)
            statements.append(stmt)
        return statements

    def _generate_create_table(self, table: DBTable) -> str:
        lines = []
        for col in table.columns:
            # Map common DB types to SQLite
            # Usually SQLite just uses TEXT, INTEGER, REAL, BLOB.
            ctype = col.type.upper()
            if "VARCHAR" in ctype or "CHAR" in ctype or "STRING" in ctype:
                ctype = "TEXT"
            elif "INT" in ctype:
                ctype = "INTEGER"
            elif "BOOL" in ctype:
                ctype = "INTEGER" # SQLite uses 0/1 for bools
            elif "FLOAT" in ctype or "DOUBLE" in ctype:
                ctype = "REAL"
            elif "DATE" in ctype or "TIME" in ctype:
                ctype = "TEXT"
                
            line_parts = [f'"{col.name}"', ctype]
            if col.primary_key:
                line_parts.append("PRIMARY KEY")
            if not col.nullable and not col.primary_key:
                line_parts.append("NOT NULL")
            if col.unique and not col.primary_key:
                line_parts.append("UNIQUE")
                
            lines.append(" ".join(line_parts))
            
        # Add foreign key constraints at the end
        for col in table.columns:
            if col.foreign_key:
                lines.append(f'FOREIGN KEY ("{col.name}") REFERENCES "{col.foreign_key.table}" ("{col.foreign_key.column}")')
                
        columns_def = ",\n    ".join(lines)
        return f'CREATE TABLE "{table.name}" (\n    {columns_def}\n);'
