def test_register_success(client):
    payload = {
        "email": "newcandidate@example.com",
        "password": "SecurePassword123!",
        "full_name": "New Candidate",
        "role": "user"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newcandidate@example.com"
    assert data["user"]["role"] == "user"

def test_register_duplicate_email(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "Password123!",
        "full_name": "Duplicate User",
        "role": "user"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

def test_login_success(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "Password123!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_user.email

def test_login_invalid_password(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "WrongPassword!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

def test_me_authenticated(client, user_auth_headers, test_user):
    response = client.get("/api/auth/me", headers=user_auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == test_user.id
    assert response.json()["email"] == test_user.email

def test_me_unauthorized(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
