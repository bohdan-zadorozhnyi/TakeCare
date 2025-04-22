from django.urls import path, include, reverse_lazy
from rest_framework.routers import DefaultRouter
from . import views
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete')
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('profile/<uuid:user_id>/', views.view_profile, name='view_profile'),
    path('edit_profile/<uuid:user_id>/', views.edit_profile, name='edit_profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
