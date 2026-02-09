# core/urls.py
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import api_views, views

app_name = 'core'

urlpatterns = [
    # ── Main / public pages ─────────────────────────────────────
    path('', views.HomeView.as_view(), name='home'),
    path('publishers/', views.PublisherListView.as_view(), name='publisher_list'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('token/', obtain_auth_token, name='api_token_auth'),

    # ── Reader features ─────────────────────────────────────────
    path('my-feed/', api_views.MyPersonalizedFeedView.as_view(), name='my-feed'),
    path('feed/subscribed/', api_views.SubscribedArticlesFeed.as_view(), name='api_feed-subscribed'),
    path('subscriptions/', views.MySubscriptionsView.as_view(), name='subscriptions'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('reader/dashboard/', views.ReaderDashboardView.as_view(), name='reader_dashboard'),

    # ── Articles ────────────────────────────────────────────────
    path('article/<int:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('article/<int:pk>/approve/', views.article_approve, name='article_approve'),
    path('article/create/', views.article_create, name='article_create'),
    path('article/<int:pk>/update/', views.article_update, name='article_update'),
    path('article/<int:pk>/delete/', views.article_delete, name='article_delete'),
    path('articles/', views.ArticleListView.as_view(), name='article_list'),

    # ── Newsletters ─────────────────────────────────────────────
    path('newsletter/<int:pk>/', views.NewsletterDetailView.as_view(), name='newsletter_detail'),
    path('newsletter/create/', views.newsletter_create, name='newsletter_create'),
    path('newsletter/<int:pk>/update/', views.newsletter_update, name='newsletter_update'),
    path('newsletter/<int:pk>/publish/', views.newsletter_publish, name='newsletter_publish'),

    # ── Publishers ──────────────────────────────────────────────
    path('publishers/<int:pk>/articles/', views.publisher_articles, name='publisher_articles'),
    path('publishers/<int:pk>/subscribe/', views.SubscribePublisherView.as_view(), name='subscribe_publisher'),

    # ── Fixed: added .as_view()
    path('publishers/<int:pk>/articles/', api_views.PublicPublisherArticles.as_view(), name='api_publisher_articles'),

    path('publishers/<int:pk>/dashboard/', views.PublisherDashboardView.as_view(), name='publisher_dashboard'),

    # ── Journalists ─────────────────────────────────────────────
    path('journalists/<str:username>/', views.JournalistProfileView.as_view(), name='journalist_profile'),
    path('journalists/<str:username>/articles/', api_views.JournalistArticlesView.as_view(),
         name='journalist_articles'),
    path('journalists/<str:username>/follow/success', views.follow_journalist, name='follow_journalist'),
    path('journalists/<str:username>/unfollow/success', views.unfollow_journalist, name='unfollow_journalist'),
    path('journalists/<str:username>/articles/', api_views.PublicJournalistArticlesView.as_view(),
         name='api_public_journalist'),
    path('journalist/dashboard/', views.JournalistDashboardView.as_view(), name='journalist_dashboard'),

    # API v1 paths
    path('api/v1/articles/<int:pk>/', api_views.ArticleDetailView.as_view(), name='api_article_detail'),
    path('api/v1/feed/subscribed/', api_views.SubscribedArticlesFeed.as_view(), name='api_subscribed_feed'),
    path('api/v1/publishers/<int:pk>/articles/', api_views.PublisherArticlesPublic.as_view(),
         name='api_publisher_articles'),
    path('api/v1/journalists/<str:username>/articles/', api_views.JournalistArticlesPublic.as_view(),
         name='api_journalist_articles')
]