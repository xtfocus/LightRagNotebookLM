import pytest
pytestmark = pytest.mark.asyncio
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

from app import crud
from app.core.security import verify_password
from app.models import User, UserCreate, UserUpdate
from app.tests.utils.utils import random_email, random_lower_string


async def test_create_user(async_db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await crud.create_user(session=async_db, user_create=user_in)
    assert user.email == email
    assert hasattr(user, "hashed_password")


async def test_authenticate_user(async_db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await crud.create_user(session=async_db, user_create=user_in)
    authenticated_user = await crud.authenticate(session=async_db, email=email, password=password)
    assert authenticated_user
    assert user.email == authenticated_user.email


async def test_not_authenticate_user(async_db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user = await crud.authenticate(session=async_db, email=email, password=password)
    assert user is None


async def test_check_if_user_is_active(async_db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await crud.create_user(session=async_db, user_create=user_in)
    assert user.is_active is True


async def test_check_if_user_is_active_inactive(async_db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, disabled=True)
    user = await crud.create_user(session=async_db, user_create=user_in)
    assert user.is_active


async def test_check_if_user_is_superuser(async_db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = await crud.create_user(session=async_db, user_create=user_in)
    assert user.is_superuser is True


async def test_check_if_user_is_superuser_normal_user(async_db: AsyncSession) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = await crud.create_user(session=async_db, user_create=user_in)
    assert user.is_superuser is False


async def test_get_user(async_db: AsyncSession) -> None:
    password = random_lower_string()
    username = random_email()
    user_in = UserCreate(email=username, password=password, is_superuser=True)
    user = await crud.create_user(session=async_db, user_create=user_in)
    user_2 = await async_db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


async def test_update_user(async_db: AsyncSession) -> None:
    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = await crud.create_user(session=async_db, user_create=user_in)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password, is_superuser=True)
    if user.id is not None:
        await crud.update_user(session=async_db, db_user=user, user_in=user_in_update)
    user_2 = await async_db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert verify_password(new_password, user_2.hashed_password)
