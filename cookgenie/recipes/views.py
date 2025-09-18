from django.shortcuts import render
from .services.firestore_service import get_all_recipes, get_recipe_by_id

def recipe_list(request):
    recipes = get_all_recipes()
    return render(request, "recipes/recipe_list.html", {"recipes": recipes})

def recipe_detail(request, recipe_id):
    recipe = get_recipe_by_id(recipe_id)
    return render(request, "recipes/detail.html", {"recipe": recipe})
