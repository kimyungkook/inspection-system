# =============================================================
# 인증 API 자동 테스트
# 회원가입/로그인/초대코드가 정상 동작하는지 자동으로 검사합니다.
# =============================================================

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_signup_success():
    """회원가입이 정상적으로 되는지 테스트"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/auth/signup", json={
            "username": "testuser01",
            "email": "test@example.com",
            "password": "TestPass123!",
        })
    assert response.status_code == 201
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_signup_duplicate_username():
    """같은 아이디로 중복 가입 시 오류 반환 테스트"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 첫 번째 가입
        await client.post("/api/v1/auth/signup", json={
            "username": "dupuser",
            "email": "dup1@example.com",
            "password": "TestPass123!",
        })
        # 같은 아이디로 두 번째 가입 시도
        response = await client.post("/api/v1/auth/signup", json={
            "username": "dupuser",
            "email": "dup2@example.com",
            "password": "TestPass123!",
        })
    assert response.status_code == 400
    assert "이미 사용 중인 아이디" in response.json()["detail"]


@pytest.mark.asyncio
async def test_signup_weak_password():
    """비밀번호 강도 검사 테스트"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/auth/signup", json={
            "username": "weakpass",
            "email": "weak@example.com",
            "password": "1234",   # 너무 짧고 단순한 비밀번호
        })
    assert response.status_code == 422   # 유효성 검사 실패


@pytest.mark.asyncio
async def test_login_success():
    """로그인 성공 및 토큰 발급 테스트"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 먼저 회원가입
        await client.post("/api/v1/auth/signup", json={
            "username": "logintest",
            "email": "login@example.com",
            "password": "TestPass123!",
        })
        # 로그인
        response = await client.post("/api/v1/auth/login", json={
            "username": "logintest",
            "password": "TestPass123!",
        })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password():
    """잘못된 비밀번호로 로그인 시도 테스트"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/auth/login", json={
            "username": "logintest",
            "password": "WrongPass999!",
        })
    assert response.status_code == 401
