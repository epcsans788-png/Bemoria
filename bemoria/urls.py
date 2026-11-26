from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from health.api import DoseLogViewSet, HealthRecordViewSet, MedicalDocumentDownloadView, MedicalDocumentViewSet, MedicationViewSet, RegisterView

router = DefaultRouter()
router.register("medications", MedicationViewSet, basename="medication")
router.register("doses", DoseLogViewSet, basename="dose")
router.register("records", HealthRecordViewSet, basename="record")
router.register("documents", MedicalDocumentViewSet, basename="document")
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/register/", RegisterView.as_view(), name="register"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/documents/<int:pk>/download/", MedicalDocumentDownloadView.as_view(), name="document-download"),
    path("api/", include(router.urls)),
    path("", include("health.urls")),
]
