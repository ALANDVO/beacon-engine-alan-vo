from collections.abc import Sequence
from typing import Any, TypeVar

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

T = TypeVar("T")


def is_async_session(session: Session | AsyncSession) -> bool:
    return isinstance(session, AsyncSession)


async def execute_async(session: AsyncSession, statement: Select) -> Any:
    return await session.execute(statement)


def execute_sync(session: Session, statement: Select) -> Any:
    return session.execute(statement)


async def execute(session: Session | AsyncSession, statement: Select) -> Any:
    if is_async_session(session):
        return await execute_async(session, statement)
    return execute_sync(session, statement)


async def scalar_async(session: AsyncSession, statement: Select) -> Any:
    return await session.scalar(statement)


def scalar_sync(session: Session, statement: Select) -> Any:
    return session.scalar(statement)


async def scalar(session: Session | AsyncSession, statement: Select) -> Any:
    if is_async_session(session):
        return await scalar_async(session, statement)
    return scalar_sync(session, statement)


async def scalars_async(session: AsyncSession, statement: Select) -> Sequence[Any]:
    result = await session.scalars(statement)
    return result.all()


def scalars_sync(session: Session, statement: Select) -> Sequence[Any]:
    result = session.scalars(statement)
    return result.all()


async def scalars(session: Session | AsyncSession, statement: Select) -> Sequence[Any]:
    if is_async_session(session):
        return await scalars_async(session, statement)
    return scalars_sync(session, statement)


async def commit_async(session: AsyncSession) -> None:
    await session.commit()


def commit_sync(session: Session) -> None:
    session.commit()


async def commit(session: Session | AsyncSession) -> None:
    if is_async_session(session):
        await commit_async(session)
    else:
        commit_sync(session)


async def refresh_async(session: AsyncSession, obj: Any) -> None:
    await session.refresh(obj)


def refresh_sync(session: Session, obj: Any) -> None:
    session.refresh(obj)


async def refresh(session: Session | AsyncSession, obj: Any) -> None:
    if is_async_session(session):
        await refresh_async(session, obj)
    else:
        refresh_sync(session, obj)


async def add_async(session: AsyncSession, obj: Any) -> None:
    session.add(obj)


def add_sync(session: Session, obj: Any) -> None:
    session.add(obj)


async def add(session: Session | AsyncSession, obj: Any) -> None:
    if is_async_session(session):
        await add_async(session, obj)
    else:
        add_sync(session, obj)


async def delete_async(session: AsyncSession, obj: Any) -> None:
    await session.delete(obj)


def delete_sync(session: Session, obj: Any) -> None:
    session.delete(obj)


async def delete(session: Session | AsyncSession, obj: Any) -> None:
    if is_async_session(session):
        await delete_async(session, obj)
    else:
        delete_sync(session, obj)