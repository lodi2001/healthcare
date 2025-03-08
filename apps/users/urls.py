from django.urls import path
from django.contrib.auth.views import LogoutView

from .views import UserTypeSelectionView, UserRegistrationView, CustomLoginView

urlpatterns = [
    path('', UserTypeSelectionView.as_view(), name='user_type_selection'),
    path('register/<str:user_type>/', UserRegistrationView.as_view(), name='user_registration'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='user_type_selection'), name='logout'),
]
