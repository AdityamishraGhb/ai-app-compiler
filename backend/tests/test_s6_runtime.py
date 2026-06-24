import pytest
from backend.schemas import DatabaseSchema, DBTable, DBColumn, ForeignKeyRef
from backend.stages.s6_runtime.simulator import RuntimeSimulator

def test_runtime_simulator_success():
    # Setup valid schema
    schema = DatabaseSchema(tables=[
        DBTable(name="users", entity="User", columns=[
            DBColumn(name="id", type="TEXT", primary_key=True, nullable=False, unique=True, foreign_key=None, comment=""),
            DBColumn(name="name", type="TEXT", primary_key=False, nullable=False, unique=False, foreign_key=None, comment="")
        ], indexes=[]),
        DBTable(name="events", entity="Event", columns=[
            DBColumn(name="id", type="TEXT", primary_key=True, nullable=False, unique=True, foreign_key=None, comment=""),
            DBColumn(name="user_id", type="TEXT", primary_key=False, nullable=False, unique=False, foreign_key=ForeignKeyRef(table="users", column="id"), comment="")
        ], indexes=[])
    ])
    
    simulator = RuntimeSimulator()
    result = simulator.execute(schema)
    
    assert result.success is True
    assert len(result.execution_errors) == 0
    assert "users" in result.tables_created
    assert "events" in result.tables_created
    assert len(result.statements_executed) == 2

def test_runtime_simulator_failure():
    # Setup invalid schema (foreign key to non-existent table)
    schema = DatabaseSchema(tables=[
        DBTable(name="events", entity="Event", columns=[
            DBColumn(name="id", type="TEXT", primary_key=True, nullable=False, unique=True, foreign_key=None, comment=""),
            DBColumn(name="user_id", type="TEXT", primary_key=False, nullable=False, unique=False, foreign_key=ForeignKeyRef(table="unknown", column="id"), comment="")
        ], indexes=[])
    ])
    
    simulator = RuntimeSimulator()
    result = simulator.execute(schema)
    
    # Wait! In SQLite, creating a table with a foreign key to a non-existent table 
    # DOES NOT fail on CREATE TABLE unless PRAGMA foreign_keys = ON AND you try to INSERT.
    # Actually, SQLite does allow creating tables referencing non-existent tables.
    # However, if we do want it to fail, we must insert data or we can just accept that SQLite is permissive.
    # Let's test a syntax error to guarantee a failure instead.
    
    schema_syntax_error = DatabaseSchema(tables=[
        DBTable(name="invalid table", entity="Event", columns=[
            DBColumn(name="id invalid", type="TEXT", primary_key=True, nullable=False, unique=True, foreign_key=None, comment="")
        ], indexes=[])
    ])
    
    # Actually wait, sqlite might accept spaces if quoted.
    # We will pass a raw string to simulator's statements instead to force failure,
    # or just use a duplicate column name.
    schema_syntax_error.tables[0].columns.append(
        DBColumn(name="id invalid", type="TEXT", primary_key=False, nullable=True, unique=False, foreign_key=None, comment="")
    )
    
    result2 = simulator.execute(schema_syntax_error)
    assert result2.success is False
    assert len(result2.execution_errors) > 0
