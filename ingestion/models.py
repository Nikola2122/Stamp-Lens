from django.db import models

# Create your models here.

class StampImage(models.Model):
    file = models.ImageField(upload_to="stamps/")
    original_name = models.CharField(max_length=255)
    extension = models.CharField(max_length=10)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name