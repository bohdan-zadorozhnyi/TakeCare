from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ObjectDoesNotExist


class EmailAuthBackend(BaseBackend):
    """Authenticate using an email and password."""

    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None  # Ensure it always returns None if authentication fails

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except (User.DoesNotExist, ObjectDoesNotExist):
            return None