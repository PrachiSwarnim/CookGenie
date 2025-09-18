from django.urls import path
from . import views

urlpatterns = [
    path("", views.recipe_list, name="recipe_list"),
    path("<str:recipe_id>/", views.recipe_detail, name="recipe_detail"),
]
