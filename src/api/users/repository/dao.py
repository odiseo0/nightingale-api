from src.api.users.domain import UserCreate, UserUpdate
from src.core.db import DAO

from .models import User


class UserDAO(DAO[User, UserCreate, UserUpdate]):
    pass


dao_users = UserDAO(User)
