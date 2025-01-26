from django.urls import path, include
from account.views import UserRegistrationView, UserLoginView, UserProfileView, UserChangePasswordView, VerifyOTPView, SendOTPView

urlpatterns = [
    path('register',UserRegistrationView.as_view(),name='register'),
    path('login',UserLoginView.as_view(),name='login'),
    path('profile',UserProfileView.as_view(),name='profile'),
    path('changePassword',UserChangePasswordView.as_view(),name='changePassword'),
    path('verify-otp', VerifyOTPView.as_view(), name='verify-otp'),
    path("send-otp", SendOTPView.as_view(), name="send_otp"),

]