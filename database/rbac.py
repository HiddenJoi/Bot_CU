from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from .models import Base
from typing import List, Dict

# Association tables
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id'))
)

class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class RBACManager:
    def __init__(self, session):
        self.session = session

    async def create_role(self, name: str, description: str = None) -> Role:
        role = Role(name=name, description=description)
        self.session.add(role)
        await self.session.commit()
        return role

    async def create_permission(self, name: str, description: str = None) -> Permission:
        permission = Permission(name=name, description=description)
        self.session.add(permission)
        await self.session.commit()
        return permission

    async def assign_role(self, user_id: int, role_name: str):
        user = await self.session.get(User, user_id)
        role = await self.session.execute(
            select(Role).where(Role.name == role_name)
        )
        role = role.scalar_one_or_none()
        
        if user and role:
            user.roles.append(role)
            await self.session.commit()

    async def grant_permission(self, role_name: str, permission_name: str):
        role = await self.session.execute(
            select(Role).where(Role.name == role_name)
        )
        role = role.scalar_one_or_none()
        
        permission = await self.session.execute(
            select(Permission).where(Permission.name == permission_name)
        )
        permission = permission.scalar_one_or_none()
        
        if role and permission:
            role.permissions.append(permission)
            await self.session.commit()

    async def check_permission(self, user_id: int, permission_name: str) -> bool:
        user = await self.session.get(User, user_id)
        if not user:
            return False
            
        for role in user.roles:
            for permission in role.permissions:
                if permission.name == permission_name:
                    return True
        return False

    async def get_user_roles(self, user_id: int) -> List[str]:
        user = await self.session.get(User, user_id)
        if not user:
            return []
        return [role.name for role in user.roles]

    async def get_role_permissions(self, role_name: str) -> List[str]:
        role = await self.session.execute(
            select(Role).where(Role.name == role_name)
        )
        role = role.scalar_one_or_none()
        if not role:
            return []
        return [permission.name for permission in role.permissions] 