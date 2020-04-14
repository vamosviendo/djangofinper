from django.urls import path

from . import views

app_name = 'finper'

urlpatterns = [
    path('', views.index, name='index'),
    path('movs/', views.MovListView.as_view(), name='movlist'),
    path('mov_sheet/', views.movsheet, name='mov_sheet'),
    path('add_movement/', views.MovCreate.as_view(), name='add_movement'),
    path('<int:pk>/mod_movement', views.MovEdit.as_view(), name='mod_mov'),
    path('<int:pk>/del_movement/', views.MovDelete.as_view(), name='del_mov'),
    path('accounts/', views.AccListView.as_view(), name='acclist'),
    path('add_account/', views.AccountCreate.as_view(), name='add_acc'),
    path('<int:pk>/mod_account/', views.AccountEdit.as_view(), name='mod_acc'),
    path('<int:pk>/del_account/', views.AccountDelete.as_view(), name='del_acc'),
    path('<int:pk>/mov_detail', views.MovDetailView.as_view(), name='movdetail'),
    path('<int:pk>/acc_detail', views.AccDetailView.as_view(), name='accdetail'),
    path('<int:pk>/check_bal', views.check_balance, name='chk_bal'),
    path('<int:pk>/balance_error', views.balance_error, name='bal_error'),
    path('<int:pk>/correct_balance', views.correct_balance, name='bal_correc'),
    path('<int:pk>/correct_start_balance',
         views.correct_start_balance,
         name='bal_start_correc'),
]
