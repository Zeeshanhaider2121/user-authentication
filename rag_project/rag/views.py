from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR)
# Manager View
def manager_view(request):
    context = {
        'role': 'Manager',
        'message': 'Welcome to the Manager Dashboard!',
        'tasks': ['Approve budgets', 'Review reports', 'Manage staff']
    }
    return render(request, 'manager.html', context)

# Staff View
def staff_view(request):
    context = {
        'role': 'Staff',
        'message': 'Welcome to the Staff Dashboard!',
        'tasks': ['Approve budgets', 'Review reports', 'Manage staff']
    }
    return render(request, 'staff.html', context)

# Employee View
def employee_view(request):
    context = {
        'role': 'Employee',
        'message': 'Welcome to the Employee Dashboard!',
        'tasks': ['Complete assigned tasks', 'Attend meetings', 'Submit reports']
    }
    return render(request, 'employee.html', context)