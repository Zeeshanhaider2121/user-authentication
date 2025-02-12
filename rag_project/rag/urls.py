from django.urls import path
from . import views

urlpatterns = [
    path('manager/', views.manager_view, name='manager'),
    path('staff/', views.staff_view, name='staff'),
    path('employee/', views.employee_view, name='employee'),
]