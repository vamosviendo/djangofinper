from django.urls import path

from . import views

app_name = 'finper'

urlpatterns = [
    path('', views.index, name='index'),
    path('movs/', views.MovListView.as_view(), name='movlist'),
    path('accounts/', views.AccListView.as_view(), name='acclist'),
    path('<int:pk>/mov_detail', views.MovDetailView.as_view(), name='movdetail'),
    path('<int:pk>/acc_detail', views.AccDetailView.as_view(), name='accdetail'),
    ]
