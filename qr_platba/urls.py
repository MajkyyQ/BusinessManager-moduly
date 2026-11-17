from django.urls import path
from . import views

app_name = "modul_qr_platba"  # adresy /moduly/qr_platba/...
urlpatterns = [path("zakazka/<int:pk>/", views.zobrazit, name="zobrazit"), path("zakazka/<int:pk>/qr.svg", views.obrazek, name="obrazek"),
               path("nastaveni/", views.nastaveni, name="nastaveni")]
