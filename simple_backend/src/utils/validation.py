import re

from src.database import UserDatabase
from src.utils.error import BadRequestError, ValidationError


class ValidationUtils:
    @staticmethod
    async def validate_email(email: str, session, skip_user_id: str = None):
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValidationError(message="Invalid email format")

        if email.lower().endswith("@gmail.com"):
            local_part = email.lower().split("@")[0].replace(".", "")
            gmail_users = await UserDatabase.filter_users_by_email_domain("gmail.com")

            for user in gmail_users:
                if skip_user_id and str(user.id) == str(skip_user_id):
                    continue

                user_local_part = user.email.lower().split("@")[0].replace(".", "")
                if user_local_part == local_part:
                    raise BadRequestError(message="Email already exists (Gmail equivalent)")
        else:
            existing_user = await UserDatabase.get_user_by_email(email=email, session= session)
            if existing_user and (not skip_user_id or str(existing_user.id) != str(skip_user_id)):
                raise BadRequestError(message="Email already exists")

        return True

    @staticmethod
    def validate_password(password: str) -> bool:
        if len(password) < 8:
            raise BadRequestError(message="Password must be at least 8 characters long")

        return True