# news_project/urls.py
"""
Main URL configuration for the News Platform project.
"""

from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ──────────────────────────────────────────────────────────────
    # Admin
    # ──────────────────────────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ──────────────────────────────────────────────────────────────
    # Authentication (standard Django paths)
    # ──────────────────────────────────────────────────────────────
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='core/login.html',
    ), name='login'),

    path('accounts/logout/', auth_views.LogoutView.as_view(
        template_name='core/logout.html',
        next_page=reverse_lazy('core:home'),
    ), name='logout'),

    # Password reset flow (highly recommended)
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='core/password_reset.html',
        email_template_name='core/password_reset_email.html',
        subject_template_name='core/password_reset_subject.txt',
    ), name='password_reset'),

    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html',
    ), name='password_reset_done'),

    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_confirm.html',
    ), name='password_reset_confirm'),

    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_complete.html',
    ), name='password_reset_complete'),

    # ──────────────────────────────────────────────────────────────
    # Core application (all main content)
    # ──────────────────────────────────────────────────────────────
    path('', include('core.urls', namespace='core')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)