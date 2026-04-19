def test_service_identity_used_for_ai_logging(auth_client):
    auth_client.post("/api/customers/query", json={"customer_description": "high value"})
    logs = auth_client.app.state.container.ai_log_repository.list_memory_logs()
    assert len(logs) >= 1
    assert logs[0]["api_execution_identity"] == "client-test"
    assert logs[0]["logged_in_user_identity"] == "tester"
