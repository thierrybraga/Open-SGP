def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_clients_requires_authentication(client):
    response = client.get("/api/clients/")
    assert response.status_code == 401


def test_public_registration_disabled_by_default(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "new-user", "email": "new-user@example.com", "password": "secret"},
    )
    assert response.status_code == 403
