def _create_user(auth_client, email: str, password: str):
    return auth_client.post(
        "/api/users/createUser",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "password": password,
        },
    )


def _login(client, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_login_success_returns_tokens(client, auth_client):
    email = "user@example.com"
    password = "StrongPass1"
    created = _create_user(auth_client, email, password)
    assert created.status_code == 201, created.text

    resp = _login(client, email, password)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str) and data["access_token"]
    assert isinstance(data["refresh_token"], str) and data["refresh_token"]
    assert data["user"]["email"] == email
    assert data["user"]["first_name"] == "Test"
    assert data["user"]["last_name"] == "User"
    assert data["user"]["role"] == "Vendedor"
    assert data["user"]["is_active"] is True


def test_login_invalid_password_fails(client, auth_client):
    email = "user2@example.com"
    password = "StrongPass1"
    created = _create_user(auth_client, email, password)
    assert created.status_code == 201, created.text

    resp = _login(client, email, "WrongPass1")
    assert resp.status_code == 401, resp.text
    assert resp.json()["message"] == "Credenciales inválidas"
    assert resp.json()["errors"] == []


def test_users_me_requires_token_and_returns_user(client, auth_client):
    email = "me@example.com"
    password = "StrongPass1"
    created = _create_user(auth_client, email, password)
    assert created.status_code == 201, created.text

    no_token = client.get("/api/users/me")
    assert no_token.status_code == 401, no_token.text

    login = _login(client, email, password)
    assert login.status_code == 200, login.text
    access = login.json()["access_token"]
    assert login.json()["user"]["email"] == email

    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200, me.text
    assert me.json()["email"] == email


def test_refresh_token_rotates_tokens(client, auth_client):
    email = "refresh@example.com"
    password = "StrongPass1"
    created = _create_user(auth_client, email, password)
    assert created.status_code == 201, created.text

    login = _login(client, email, password)
    assert login.status_code == 200, login.text
    refresh_token = login.json()["refresh_token"]

    refreshed = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200, refreshed.text
    data = refreshed.json()

    assert data["token_type"] == "bearer"
    assert data["access_token"] != login.json()["access_token"]
    assert data["refresh_token"] != refresh_token
