from rest_framework.response import Response
from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from account.serializers import UserSerializer, UserRegistrationSerializer, VerifyOTPSerializer, UserLoginSerializer, UserProfileSerializer, UserChangePasswordSerializer, OTPVerifySerializer, OTPSendSerializer
from django.contrib.auth import authenticate
from account.renderers import UserRenderer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from account.utils import create_and_send_otp 
from .models import EmailOTP
from django.contrib.auth import  get_user_model
from rest_framework.permissions import AllowAny, IsAdminUser

User = get_user_model()


# Generate Token manually
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            create_and_send_otp(user, purpose="register")
            return Response(
                {"detail": "Account created. Check email for OTP to verify your account."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyRegistrationOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp_text = serializer.validated_data["otp"]
        purpose = serializer.validated_data["purpose"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # find OTP
        try:
            otp = EmailOTP.objects.filter(user=user, otp=otp_text, purpose=purpose, used=False).latest("created_at")
        except EmailOTP.DoesNotExist:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response({"detail": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

        otp.mark_used()
        if purpose == "register":
            user.is_active = True
            user.save()
            return Response({"detail": "Account verified. You can login now."})
        else:
            return Response({"detail": "OTP verified."})

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        # check password and active state
        if not user.check_password(password):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"detail": "Account not activated. Verify your email first."}, status=status.HTTP_403_FORBIDDEN)

        # generate and send OTP for login
        create_and_send_otp(user, purpose="login")
        return Response({"detail": "OTP sent to email. Use verify-login-otp endpoint to finish login."})

class VerifyLoginOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp_text = serializer.validated_data["otp"]
        purpose = serializer.validated_data["purpose"]

        if purpose != "login":
            return Response({"detail": "Purpose must be 'login' for this endpoint."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # find OTP
        try:
            otp = EmailOTP.objects.filter(user=user, otp=otp_text, purpose=purpose, used=False).latest("created_at")
        except EmailOTP.DoesNotExist:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response({"detail": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

        otp.mark_used()
        # issue tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        })

    
class UserProfileView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data ,status=status.HTTP_200_OK)
    
class UserChangePasswordView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        serializer = UserChangePasswordSerializer(data=request.data, context = {'user':request.user})
        if serializer.is_valid(raise_exception=True):
            return Response({'msg':'Password Changed successfully!'},status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "OTP verified successfully. Your account is now active."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class SendOTPView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = OTPSendSerializer(data=request.data)
        if serializer.is_valid():
            try:
                response_data = serializer.create_otp_and_send()
                return Response(response_data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)