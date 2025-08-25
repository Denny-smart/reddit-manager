from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('POSTER', 'Poster'),
        ('VIEWER', 'Viewer'),   # ✅ Added Viewer role
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='VIEWER')  # Default = Viewer

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# ✅ Automatically create/update profile when user is created
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_superuser:
            Profile.objects.create(user=instance, role='ADMIN')   # Superuser → Admin
        else:
            Profile.objects.create(user=instance, role='VIEWER')  # Normal user → Viewer
    else:
        instance.profile.save()
