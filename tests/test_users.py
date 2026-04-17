def test_create_user_defaults_to_non_admin(client):
    payload = {
        "first_name": "Juan",
        "last_name": "Perez",
        "email": " JUAN.PEREZ@EXAMPLE.COM ",
        "password": "StrongPass1",
        "is_admin": True,  # should be ignored server-side
    }

    resp = client.post("/api/users/createUser", json=payload)
    assert resp.status_code == 201, resp.text

    data = resp.json()
    assert data["email"] == "juan.perez@example.com"
    assert data["first_name"] == "Juan"
    assert data["last_name"] == "Perez"
    assert data["is_admin"] is False
    assert data["role"] == "Vendedor"


def test_create_admin_only_once(client):
    payload = {
        "first_name": "Admin",
        "last_name": "One",
        "email": "admin@example.com",
        "password": "StrongPass1",
    }

    first = client.post("/api/users/createAdmin", json=payload)
    assert first.status_code == 201, first.text
    assert first.json()["is_admin"] is True
    assert first.json()["role"] == "Administrador"

    second = client.post(
        "/api/users/createAdmin",
        json={
            "first_name": "Admin",
            "last_name": "Two",
            "email": "admin2@example.com",
            "password": "StrongPass1",
        },
    )
    assert second.status_code == 409, second.text
    assert second.json()["message"] == "Ya existe un usuario administrador"
    assert second.json()["errors"] == []


def test_user_can_be_deactivated_and_reactivated(client):
    created = client.post(
        "/api/users/createUser",
        json={
            "first_name": "Ana",
            "last_name": "Lopez",
            "email": "ana.lopez@example.com",
            "password": "StrongPass1",
        },
    )
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]
    assert created.json()["is_active"] is True

    deactivated = client.delete(f"/api/users/delete/{user_id}")
    assert deactivated.status_code == 200, deactivated.text
    assert deactivated.json()["is_active"] is False

    reactivated = client.patch(
        f"/api/users/status/{user_id}",
        json={"is_active": True},
    )
    assert reactivated.status_code == 200, reactivated.text
    assert reactivated.json()["is_active"] is True


def test_create_user_rejects_invalid_role(client):
    created = client.post(
        "/api/users/createUser",
        json={
            "first_name": "Mario",
            "last_name": "Suarez",
            "email": "mario.suarez@example.com",
            "password": "StrongPass1",
            "role": "Gerente",
        },
    )

    assert created.status_code == 422, created.text
    data = created.json()
    assert data["message"] == "Error de validación"
    assert any(error["field"] == "role" for error in data["errors"])


def test_update_user_can_change_role(client):
    created = client.post(
        "/api/users/createUser",
        json={
            "first_name": "Luisa",
            "last_name": "Mendez",
            "email": "luisa.mendez@example.com",
            "password": "StrongPass1",
            "role": "Vendedor",
        },
    )
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]

    updated = client.put(
        f"/api/users/update/{user_id}",
        json={"role": "Mixto"},
    )

    assert updated.status_code == 200, updated.text
    assert updated.json()["role"] == "Mixto"
