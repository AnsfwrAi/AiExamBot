import secrets
import re
import string
from django.db import models
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from datetime import timedelta
import random


def generate_key(length=28):
    return secrets.token_urlsafe(length)[:length]

def generate_unique_script_name():
    alphabet = string.ascii_lowercase
    base_length = 3
    max_attempts = 100
    attempts = 0

    while attempts < max_attempts:
        name = ''.join(random.choices(alphabet, k=base_length))
        if not IdScript.objects.filter(script=name).exists():
            return name
        attempts += 1

    base_name = ''.join(random.choices(alphabet, k=base_length))
    suffix = 1
    while True:
        name = f"{base_name}{suffix}"
        if not IdScript.objects.filter(script=name).exists():
            return name
        suffix += 1

def validate_script_name(value):
    if not re.match(r'^[a-zA-Z0-9_\-]+$', value):
        raise ValidationError("Поле 'script' может содержать только латинские буквы, цифры, дефис и подчёркивание.")


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class TgUserPolice(models.Model):
    police = models.BooleanField(default=False)

    class Meta:
        abstract = True


class TgUsers(BaseModel, TgUserPolice):
    user = models.BigIntegerField(unique=True)
    is_admin = models.BooleanField(default=False)
    username = models.CharField(max_length=255, null=True, blank=True)

    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referred_users',
        verbose_name='Пригласил',
        help_text='Пользователь, который пригласил данного пользователя'
    )

    LANGUAGE_CHOICES = [
        ('ru', 'Russian'),
        ('uz', 'Uzbek'),
    ]
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='ru'
    )

    def __str__(self):
        return f"{f'{self.username} - {self.user}' if self.username else self.user}"

    @property
    def referral_count(self):
        return self.referred_users.count()

    @property
    def has_referrer(self):
        return self.referred_by is not None

    def set_language(self, lang):
        if lang in dict(self.LANGUAGE_CHOICES):
            self.language = lang
            self.save()
            return True
        return False


class IdScript(BaseModel):
    class ScriptChoices(models.TextChoices):
        BASE_PROD_UUID = 'base_prod_uuid', 'Base production script with UUID'
        BASE_PROD = 'base_prod', 'Base production script'
        V2_VIEWPORT_CROP = 'v2_viewport_crop', 'V2 - надежный кроп (снимок всего экрана + обрезка)'

    owner = models.ForeignKey(
        TgUsers,
        on_delete=models.CASCADE,
        related_name='scripts',
    )

    script = models.CharField(
        max_length=100,
        unique=True,
        validators=[validate_script_name],
        help_text="Имя JS-файла (короткое и человекочитаемое)",
        blank=True,
        db_index=True
    )
    key = models.CharField(
        max_length=28,
        unique=True,
        blank=True,
        db_index=True
    )
    script_type = models.CharField(
        max_length=100,
        choices=ScriptChoices.choices,
        default=ScriptChoices.BASE_PROD
    )
    fingerprint = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True
    )

    start_at = models.DateTimeField(db_index=True)
    stop_at = models.DateTimeField(db_index=True)
    is_active = models.BooleanField(default=False, db_index=True)
    used = models.IntegerField(default=0)
    max_usage = models.IntegerField(default=75)
    first_activate = models.DateTimeField(null=True, blank=True)
    first_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'start_at', 'stop_at']),
            models.Index(fields=['fingerprint', 'is_active']),
        ]

    def __str__(self):
        return self.script

    def is_within_active_time(self) -> bool:
        current_time = now()
        return self.is_active and self.start_at <= current_time <= self.stop_at

    def is_usage_available(self) -> bool:
        return self.used < self.max_usage

    # def initialize_activation_if_needed(self):
    #     if not self.first_activate:
    #         current_time = now()
    #         IdScript.objects.filter(
    #             id=self.id,
    #             first_seen__isnull=True
    #         ).update(first_seen=current_time)
    #         self.first_activate = current_time

    def initialize_activation_if_needed(self):
        if not self.first_activate:
            current_time = now()
            IdScript.objects.filter(
                id=self.id,
                first_activate__isnull=True
            ).update(
                first_activate=current_time,
                first_seen=current_time
            )
            self.first_activate = current_time
            self.first_seen = current_time

    def is_fingerprint_valid(self, fp: str) -> bool:
        return self.fingerprint == fp

    def assign_fingerprint_if_unset(self, fp: str) -> bool:
        if not self.fingerprint:
            updated = IdScript.objects.filter(
                id=self.id,
                fingerprint__isnull=True
            ).update(fingerprint=fp)
            if updated:
                self.fingerprint = fp
                return True
        return False

    def is_ready_to_assign_fingerprint(self) -> bool:
        if not self.first_activate:
            return False
        return now() - self.first_activate >= timedelta(seconds=20)

    def try_bind_fingerprint(self, fp: str) -> bool:
        if self.is_ready_to_assign_fingerprint():
            return self.assign_fingerprint_if_unset(fp)
        return True

    def increment_usage(self):
        IdScript.objects.filter(id=self.id).update(used=models.F('used') + 1)
        self.used += 1

    @property
    def is_max_usage_reached(self):
        return self.used >= self.max_usage

    def save(self, *args, **kwargs):
        if not self.script:
            self.script = generate_unique_script_name()
        if not self.key:
            self.key = generate_key()
        if not self.fingerprint:
            self.fingerprint = generate_key(32)
        super().save(*args, **kwargs)


class Answer(BaseModel):
    script = models.ForeignKey(
        IdScript,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    image = models.ImageField(upload_to='images/')
    answer = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['script', 'created_at']),
        ]

    def __str__(self):
        return f"{self.script.script} - {self.created_at}"



class Referral(models.Model):
    inviter = models.ForeignKey(TgUsers, on_delete=models.CASCADE, related_name='invited')
    invited = models.ForeignKey(TgUsers, on_delete=models.CASCADE, related_name='referral_source')
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.inviter} → {self.invited} | Used: {self.used}"



