# -*- coding: utf-8 -*-
# FileName: base.py
# Time : 2024/6/13 9:09
# Author: zzy
# -*- coding: utf-8 -*-
# FileName: base.py
# Time : 2023/8/3 16:32
# Author: zzy
from typing import (
    Any, Dict,
    Generic, Optional, Type,
    TypeVar, Union, Sequence
)

from pydantic import BaseModel
from sqlalchemy import select, Row, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import BaseOrmTable

ModelType = TypeVar("ModelType", bound=BaseOrmTable)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    这里我们定义了一个泛型类, 允许的类型 -> [
        ModelType, CreateSchemaType, UpdateSchemaType
    ]
    分别是一个用于数据库的sqlalchemy模型类 -> ModelType
    一个用于 新建用户/更新用户 的pydantic模型类 -> ModelType / UpdateSchemaType
    """

    def __init__(self, model: Type[ModelType]):
        """
        默认方法: create - select - update - delete

        * `model`: 一个`sqlalchemy base` 类
        * `schema`: 一个 `pydantic` 模型 / 类
        """
        self.model = model

    async def get(self, async_session: AsyncSession, _id: Any) -> Optional[ModelType]:
        result = await async_session.execute(select(self.model).where(self.model.id == _id))
        # 如果是sa2.0的asyncOrm情况下显式指定 -> selectinload(UserOrm.plants)
        # 可以独立调用此方法selectinload().lazyload(PlantOrm.diseases) -> 仅适用于关系(一对多,多对多)字段
        return result.scalars().first()

    async def get_with_relations(
            self,
            async_session: AsyncSession,
            _id: int,
            *relationship_fields: str
    ) -> Optional[ModelType]:
        """
        获取该模型的所有关系字段, 此方法可重载
        :param async_session: 会话
        :param _id: 主键
        :param relationship_fields: 字段名称
        :return:
        """
        result = await async_session.execute(
            select(self.model)
            .where(self.model.id == _id)
            .options(
                *[selectinload(getattr(self.model, rf)) for rf in relationship_fields]
            )
        )
        return result.scalars().first()

    async def get_multi(
            self, async_session: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> Sequence[Row | RowMapping | Any]:
        result = await async_session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, async_session: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        async with async_session.begin():
            db_obj = self.model(**obj_in.dict())
            async_session.add(db_obj)
            return db_obj

    async def update(
            self,
            async_session: AsyncSession,
            *,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        通过接收用户请求更新字段, 查找当前用户后按照用户提供字段做变更
        :param async_session: 会话
        :param db_obj: 当前用户old
        :param obj_in: 用户提供更新字段new
        :return:
        """
        result = await async_session.execute(select(self.model).where(self.model.id == db_obj.id))
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            print(update_data)
        user = result.scalars().first()

        for field, val in update_data.items():
            setattr(user, field, val)

        await async_session.commit()
        return user

    async def remove(self, async_session: AsyncSession, *, _id: int) -> None:
        stmt = await async_session.execute(select(self.model).where(self.model.id == _id))
        result = stmt.scalar_one()
        user = await async_session.delete(
            result
        )
        await async_session.flush()
        await async_session.commit()