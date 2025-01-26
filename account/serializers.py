from xml.dom import ValidationErr
from rest_framework import serializers
from account.models import User, UserOTPVerification
from django.utils.encoding import smart_str, force_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from account.utils import Util
import random
from django.utils import timezone
from datetime import timedelta

class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type':'password'}, write_only=True)
    class Meta:
        model = User
        fields=['email', 'name', 'password', 'password2', 'tc']
        extra_kwargs={
        'password':{'write_only':True}
        }

    # Validating Password and Confirm Password while Registration
    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError("Password and Confirm Password doesn't match")
        return attrs

    def create(self, validated_data):
        # Create the User object
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password'],
            tc=validated_data['tc']
        )

        user.is_active = True
        user.save()

        # # Generate OTP
        # otp = random.randint(100000, 999999)

        # # Create OTP verification record
        # otp_verification = UserOTPVerification.objects.create(
        #     user=user,
        #     otp=otp,
        #     expires_at=timezone.now() + timedelta(minutes=5)  # OTP expiration set to 5 minutes
        # )
        
        # #Send Email
        # body = f'Your OTP is {otp}. It will expire in 5 minutes.'
        # data = {
        #     'subject':'Your OTP for Signup Verification',
        #     'body':body,
        #     'to_email':user.email
        # }
        # Util.send_email(data)

        return user

class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
    class Meta:
        model = User
        fields = ['email', 'password']
    
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email','name']
        
class UserChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=255, style={'input_type':'password'}, write_only=True)
    password2 = serializers.CharField(max_length=255, style={'input_type':'password'}, write_only=True)
    class Meta:
        fields = ['password','password2']
    
    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        user = self.context.get('user')
        if password != password2:
            raise serializers.ValidationError("Password and Confirm Password doesn't match")
        user.set_password(password) 
        user.save()
        return super().validate(attrs)

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()

    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')

        # Retrieve the user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email address.")

        # Retrieve the most recent OTP record for this user
        try:
            otp_record = UserOTPVerification.objects.filter(user=user, is_verified=False).latest('created_at')
        except UserOTPVerification.DoesNotExist:
            raise serializers.ValidationError("No OTP record found for this user.")

        # Check if OTP is expired
        if otp_record.is_expired():
            raise serializers.ValidationError("The OTP has expired. Please request a new one.")

        # Check if the provided OTP is correct
        if otp_record.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")

        # OTP is valid, mark it as verified
        otp_record.is_verified = True
        otp_record.save()

        # Activate the user's account
        user.is_active = True
        user.save()

        return user
    
class OTPSendSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Check if the email exists in the User table
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("This email is not registered with us.")
        return value

    def create_otp_and_send(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)  # Fetch user for email content personalization

        # Generate OTP
        otp = random.randint(100000, 999999)

        # Create OTP verification record
        otp_verification = UserOTPVerification.objects.create(
            user=user,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=5)  # OTP expiration set to 5 minutes
        )
         
        #Send Email
        body = f'Your OTP is {otp}. It will expire in 5 minutes.'
        data = {
            'subject':'Your OTP for Signup Verification',
            'body':body,
            'to_email':user.email
        }
        try:
            Util.send_email(data)
        except Exception as e:
            raise serializers.ValidationError(f"Failed to send OTP: {str(e)}")
        return {"msg": "OTP sent successfully"}