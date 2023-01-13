from django.urls import include, path

from .views import authViews, dataViews, formViews
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', dataViews.index, name='index'),
    path('addDepartment', formViews.addDepartment, name='addDepartment'),
    path('login', auth_views.LoginView.as_view(template_name = 'registration/login.html'), name = 'login'),
    path('logout', authViews.logout_view, name = 'logout'),
    path('register', authViews.register, name = 'register'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('successPage', authViews.successPage, name="successPage"),
    path('activate/<uidb64>/<token>', authViews.activate, name='activate'),
    path('departments', dataViews.departments, name="departments"),
    path('departmentChange', dataViews.departmentChange, name="departmentChange"),
    path('teachers', dataViews.teachers, name="teachers"),
    path('teacherChange', dataViews.teacherChange, name='teacherChange'),
    path('addTeacher/<int:department>', formViews.addTeacher, name='addTeacher'),
    path('addTeacher/<int:department>/<int:id>', formViews.addTeacher, name='addTeacher'),
    path('viewObjects/<str:type>', dataViews.viewObjects, name='viewObjects'),
    path('viewObjects/<str:type>/<int:id>', dataViews.viewObjects, name='viewObjects'),
    path('getTeacher/<int:id>', dataViews.getTeacher, name='getTeacher'),
    path('setAvailability/<int:teacherid>', formViews.setAvailability, name='setAvailability'),
    path('modules/<int:departmentId>', dataViews.modules, name="modules"),
    path('viewModules/<str:type>/<int:departmentId>/<int:id>', dataViews.viewModules, name="viewModules"),
    path('viewModules/<str:type>/<int:departmentId>', dataViews.viewModules, name="viewModules"),
    path('addModule/<int:year>', formViews.addModule, name="addModule"),
    path('addYear/<int:departmentId>', formViews.addYear, name="addYear"),
    path('getModules/<int:id>', dataViews.getModules, name='getModules'),
    path('assignTeacher/<int:departmentId>/<int:moduleId>', formViews.assignTeacher, name='assignTeacher'),
]