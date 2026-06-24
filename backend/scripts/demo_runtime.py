from backend.schemas import DatabaseSchema, DBTable, DBColumn, ForeignKeyRef
from backend.stages.s6_runtime.simulator import RuntimeSimulator

def run_demo():
    print("=" * 60)
    print("RUNTIME SIMULATOR - LIVE DEMO (0 LLM Calls)")
    print("=" * 60)

    # Mock DatabaseSchema
    schema = DatabaseSchema(tables=[
        DBTable(name="users", entity="User", columns=[
            DBColumn(name="id", type="TEXT", primary_key=True, nullable=False, unique=True, foreign_key=None, comment=""),
            DBColumn(name="email", type="TEXT", primary_key=False, nullable=False, unique=True, foreign_key=None, comment="")
        ], indexes=[]),
        DBTable(name="events", entity="Event", columns=[
            DBColumn(name="id", type="TEXT", primary_key=True, nullable=False, unique=True, foreign_key=None, comment=""),
            DBColumn(name="name", type="TEXT", primary_key=False, nullable=False, unique=False, foreign_key=None, comment="")
        ], indexes=[]),
        DBTable(name="songs", entity="Song", columns=[
            DBColumn(name="id", type="TEXT", primary_key=True, nullable=False, unique=True, foreign_key=None, comment=""),
            DBColumn(name="title", type="TEXT", primary_key=False, nullable=False, unique=False, foreign_key=None, comment="")
        ], indexes=[])
    ])

    simulator = RuntimeSimulator()
    result = simulator.execute(schema)

    print("\nTables Generated:")
    for table in result.tables_created:
        print(f"* {table}")

    print(f"\nExecution:\n{'SUCCESS' if result.success else 'FAILED'}")

    if not result.success:
        print("\nErrors:")
        for error in result.execution_errors:
            print(error)

if __name__ == "__main__":
    run_demo()
