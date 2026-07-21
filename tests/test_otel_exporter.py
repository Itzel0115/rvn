from observability.exporter import SQLiteSpanExporter
from observability.store import SQLiteTraceStore

def test_exporter_failure_is_non_throwing(tmp_path):
    exporter=SQLiteSpanExporter(SQLiteTraceStore(tmp_path/"traces.sqlite3"))
    assert exporter.export([object()]).name=="FAILURE"
