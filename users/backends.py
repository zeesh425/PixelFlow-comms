from django.contrib.auth.backends import ModelBackend
from users.models import CustomUser

class ApprovedUserBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print("AUTH BACKEND: authenticate called")
        print(f"Username: {username}")

        try:
            user = CustomUser.objects.get(username=username)
            print(f"User found: {user.username} | is_superuser: {user.is_superuser} | is_approved: {user.is_approved}")

            if user.check_password(password):
                print("Password is correct")

                if user.is_superuser or user.is_approved:
                    print("Authentication success")
                    return user
                else:
                    print("User not approved")
            else:
                print("Invalid password")

        except CustomUser.DoesNotExist:
            print("User not found")

        print("Authentication failed")
        return None
