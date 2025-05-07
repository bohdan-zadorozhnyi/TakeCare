from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.article_list, name='article_list'),
    path('create/', views.article_create, name='article_create'),
    path('<uuid:pk>/edit/', views.article_edit, name='article_edit'),
    path('<uuid:pk>/delete/', views.article_delete, name='article_delete'),
    path('<uuid:article_id>/', views.article_detail_view, name='article_detail')
]