from django.contrib.auth import views as auth_views
from django.urls import path
from .views import (
    clinic_delete, clinic_list, dashboard, dose_history, emergency_card, health_area,
    health_condition_delete, health_record_create, health_record_list, mark_dose_taken,
    medical_document_delete, medical_document_download, medical_document_list,
    medication_create, medication_delete, medication_list, medication_update,
    profile, profile_photo, register,
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("register/", register, name="register-page"),
    path("medicamentos/", medication_list, name="medication-list"),
    path("medicamentos/novo/", medication_create, name="medication-create"),
    path("medicamentos/<int:pk>/editar/", medication_update, name="medication-update"),
    path("medicamentos/<int:pk>/remover/", medication_delete, name="medication-delete"),
    path("medicamentos/horarios/<int:schedule_id>/tomar/", mark_dose_taken, name="mark-dose-taken"),
    path("historico/", health_record_list, name="record-list"),
    path("historico/novo/", health_record_create, name="record-create"),
    path("historico/doses/", dose_history, name="dose-history"),
    path("perfil/", profile, name="profile"),
    path("perfil/foto/", profile_photo, name="profile-photo"),
    path("emergencia/", emergency_card, name="emergency-card"),
    path("documentos/", medical_document_list, name="document-list"),
    path("documentos/<int:pk>/baixar/", medical_document_download, name="document-download-ui"),
    path("documentos/<int:pk>/remover/", medical_document_delete, name="document-delete"),
    path("saude/", health_area, name="health-area"),
    path("saude/condicoes/<int:pk>/remover/", health_condition_delete, name="condition-delete"),
    path("clinicas/", clinic_list, name="clinic-list"),
    path("clinicas/<int:pk>/remover/", clinic_delete, name="clinic-delete"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("senha/esqueci/", auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html", email_template_name="registration/password_reset_email.html", subject_template_name="registration/password_reset_subject.txt"), name="password_reset"),
    path("senha/enviado/", auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("senha/redefinir/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("senha/concluido/", auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),
]
