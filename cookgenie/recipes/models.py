from django.db import models

class Recipe(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    ingredients = models.TextField()
    instructions = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    source_url = models.URLField()

    def __str__(self):
        return self.title