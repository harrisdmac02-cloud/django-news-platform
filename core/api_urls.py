from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    path('my-feed/', api_views.MyPersonalizedFeedView.as_view(), name='my-feed'),
    path('articles/', api_views.ArticleListView.as_view(), name='article-list'),
    path('articles/<int:id>/', api_views.ArticleDetailView.as_view(), name='article-detail'),
    path('publishers/<int:pk>/articles/', api_views.PublisherArticlesView.as_view(), name='publisher-articles'),
    path('journalists/<str:username>/articles/', api_views.JournalistArticlesView.as_view(), name='journalist-articles'),
]