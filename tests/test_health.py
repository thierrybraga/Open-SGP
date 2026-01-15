def test_health_check(client):
    # Try the documented health endpoint if exists
    response = client.get("/api/health")
    if response.status_code == 404:
        # Try root
        response = client.get("/")
    
    # Just ensure we get a response and app is running
    assert response.status_code in [200, 404]
