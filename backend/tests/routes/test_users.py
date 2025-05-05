import pytest
from fastapi import status
from backend.models.otp import OTP, OTPPurpose
from datetime import datetime, timedelta, timezone
from backend.schemas.user import UserCreate

def test_register_user(client, db):
    user_data = {
        "email": "delivered@resend.dev",
        "password": "testpass123",
        "name": "New User"
    }
    
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["name"] == user_data["name"]
    assert "password" not in data
    
    # Verify OTP was created
    otp = db.query(OTP).filter(OTP.email == user_data["email"]).first()
    assert otp is not None
    assert otp.purpose == OTPPurpose.REGISTRATION

def test_register_duplicate_user(client, test_user):
    user_data = {
        "email": "delivered@resend.dev",  # Same email as test_user
        "password": "testpass123",
        "name": "Duplicate User"
    }
    
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_success(client, test_user):
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    
    response = client.post("/users/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_invalid_credentials(client):
    login_data = {
        "email": "wrong@test.com",
        "password": "wrongpass"
    }
    
    response = client.post("/users/login", json=login_data)
    assert response.status_code == 404

def test_get_current_user(authorized_client, test_user):
    response = authorized_client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["name"] == test_user["name"]

def test_request_otp_registration(client):
    otp_request = {
        "email": "delivered@resend.dev",
        "purpose": "registration"  # Using the enum value string
    }
    
    response = client.post("/users/request-otp", json=otp_request)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["expires_in"] == 300

def test_request_otp_password_reset(client, test_user):
    otp_request = {
        "email": test_user["email"],  # This will be delivered@resend.dev from the fixture
        "purpose": "password_reset"  # Using the enum value string
    }
    
    response = client.post("/users/request-otp", json=otp_request)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["expires_in"] == 300

def test_verify_email(client, db, test_user):
    # Create an OTP for verification
    otp_code = "12345"
    otp = OTP(
        id="test_id",
        email=test_user["email"],
        code=otp_code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        purpose=OTPPurpose.REGISTRATION
    )
    db.add(otp)
    db.commit()

    verify_data = {
        "email": test_user["email"],
        "code": otp_code
    }
    
    response = client.post("/users/verify-email", json=verify_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_reset_password(client, db, test_user):
    # Create an OTP for password reset
    otp_code = "12345"
    otp = OTP(
        id="test_id",
        email=test_user["email"],
        code=otp_code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        purpose=OTPPurpose.PASSWORD_RESET
    )
    db.add(otp)
    db.commit()

    reset_data = {
        "email": test_user["email"],
        "code": otp_code,
        "new_password": "newpassword123"
    }
    
    response = client.post("/users/reset-password", json=reset_data)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    
    # Try logging in with new password
    login_data = {
        "email": test_user["email"],
        "password": "newpassword123"
    }
    
    login_response = client.post("/users/login", json=login_data)
    assert login_response.status_code == 200

def test_invalid_otp_verification(client, test_user):
    verify_data = {
        "email": test_user["email"],
        "code": "wrong_code"
    }
    
    response = client.post("/users/verify-email", json=verify_data)
    assert response.status_code == 400
    assert "Invalid or expired OTP" in response.json()["detail"]

def test_expired_otp(client, db, test_user):
    # Create an expired OTP
    otp_code = "12345"
    otp = OTP(
        id="test_id",
        email=test_user["email"],
        code=otp_code,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=10),  # expired
        purpose=OTPPurpose.REGISTRATION
    )
    db.add(otp)
    db.commit()

    verify_data = {
        "email": test_user["email"],
        "code": otp_code
    }
    
    response = client.post("/users/verify-email", json=verify_data)
    assert response.status_code == 400
    assert "Invalid or expired OTP" in response.json()["detail"] 