from django.urls import path
from . import views

app_name = "modul_email"  # adresy /moduly/email/...
urlpatterns = [path("odeslat/", views.odeslat_stranka, name="odeslat"), path("nastaveni/", views.nastaveni, name="nastaveni"),
               path("odeslane/", views.odeslane, name="odeslane")]
