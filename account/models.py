from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils.timezone import now
from datetime import timedelta


class UserManager(BaseUserManager):
    def create_user(self, email, name, tc, password=None):
        """
        Creates and saves a User with the given email, name, password and tc.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            name=name,
            tc=tc,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, tc, password=None):
        """
        Creates and saves a User with the given email, name, password, and tc.
        """
        user = self.create_user(
            email,
            password=password,
            name=name,
            tc=tc,
        )
        user.is_admin = True
        user.is_active = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name="Email",
        max_length=255,
        unique=True,
    )
    name = models.CharField(max_length=200)
    tc = models.BooleanField()
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "tc"]

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        return self.is_admin

    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        return True

    @property
    def is_staff(self):
        """Is the user a member of staff?"""
        return self.is_admin

class UserOTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_verifications')
    otp = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Automatically set expiration time if not provided
        if not self.expires_at:
            self.expires_at = now() + timedelta(minutes=5)  # Set OTP expiration time to 5 minutes
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if the OTP has expired."""
        return now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.user.email}: {self.otp} (Expires at {self.expires_at})"
