import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate
from app.core.retry_utils import db_retry


@db_retry
async def _commit_user_transaction(session: AsyncSession):
    """Commit user transaction with retry logic."""
    await session.commit()

@db_retry
async def _commit_item_transaction(session: AsyncSession):
    """Commit item transaction with retry logic."""
    await session.commit()


async def create_user(*, session: AsyncSession, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    await _commit_user_transaction(session)
    await session.refresh(db_obj)
    return db_obj


async def update_user(*, session: AsyncSession, db_obj: User, obj_in: UserUpdate) -> User:
    update_data = obj_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    await _commit_user_transaction(session)
    await session.refresh(db_obj)
    return db_obj


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    session_user = result.scalars().first()
    return session_user


async def authenticate(*, session: AsyncSession, email: str, password: str) -> User | None:
    db_user = await get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


async def create_item(*, session: AsyncSession, item_create: ItemCreate, owner_id: int) -> Item:
    db_obj = Item.model_validate(item_create, update={"owner_id": owner_id})
    session.add(db_obj)
    await _commit_item_transaction(session)
    await session.refresh(db_obj)
    return db_obj
