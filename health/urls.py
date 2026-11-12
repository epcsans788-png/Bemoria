from django.contrib.auth import views as auth_views
from django.urls import path
from .views import dashboard, health_record_create, health_record_list, mark_dose_taken, medication_create, medication_delete, medication_list, register

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("register/", register, name="register-page"),
    path("medicamentos/", medication_list, name="medication-list"),
    path("medicamentos/novo/", medication_create, name="medication-create"),
    path("medicamentos/<int:pk>/remover/", medication_delete, name="medication-delete"),
    path("medicamentos/horarios/<int:schedule_id>/tomar/", mark_dose_taken, name="mark-dose-taken"),
    path("historico/", health_record_list, name="record-list"),
    path("historico/novo/", health_record_create, name="record-create"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
