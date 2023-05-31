from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import User


class Message(models.Model):
    id = models.UUIDField(editable=False, primary_key=True)
    author = models.ForeignKey(User, models.CASCADE)
    receive = models.DateTimeField(editable=False)


class Channel(models.Model):
    name = models.CharField(max_length=150, validators=[UnicodeUsernameValidator]) # the same rules
    id = models.UUIDField(editable=False, primary_key=True)
    owner = models.ForeignKey(User, models.CASCADE, related_name='+')
    members = models.ManyToManyField(User, related_name='+')
    admins = models.ManyToManyField(User, related_name='+')
    messages = models.ManyToManyField(Message, related_name='+')