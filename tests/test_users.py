def test_create_user_defaults_to_non_admin(client):
    payload = {
        "first_name": "Juan",
        "last_name": "Perez",
        "email": " JUAN.PEREZ@EXAMPLE.COM ",
        "password": "StrongPass1",
        "is_admin": True,  # should be ignored server-side
    }

    resp = client.post("/users/createUser", json=payload)
    assert resp.status_code == 201, resp.text

    data = resp.json()
    assert data["email"] == "juan.perez@example.com"
    assert data["first_name"] == "Juan"
    assert data["last_name"] == "Perez"
    assert data["is_admin"] is False


def test_create_admin_only_once(client):
    payload = {
        "first_name": "Admin",
        "last_name": "One",
        "email": "admin@example.com",
        "password": "StrongPass1",
    }

    first = client.post("/users/createAdmin", json=payload)
    assert first.status_code == 201, first.text
    assert first.json()["is_admin"] is True

    second = client.post(
        "/users/createAdmin",
        json={
            "first_name": "Admin",
            "last_name": "Two",
            "email": "admin2@example.com",
            "password": "StrongPass1",
        },
    )
    assert second.status_code == 409, second.text
    assert second.json()["detail"] == "An admin user already exists"

