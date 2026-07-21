from mcp_server import server

def test_mcp_module_import_does_not_start_server_or_expose_write_tools():
    assert server.mcp is not None
    assert not any(name in server.__dict__ for name in ("approve", "publish", "execute_sql", "run_python"))
