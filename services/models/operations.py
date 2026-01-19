from datetime import datetime
from django.forms.models import model_to_dict
from datetime import timedelta
from django.utils import timezone

from api.v1 import models
from . import catch_error


@catch_error("ERR_GET_OR_CREATE_USER")
def get_or_create_tg_user(user_id: int, ref_by: int = None) -> dict:
    user, created = models.TgUsers.objects.get_or_create(user=user_id)

    if created and ref_by:
        try:
            ref_user = models.TgUsers.objects.get(user=ref_by)
            user.referred_by = ref_user
            user.save()
        except models.TgUsers.DoesNotExist:
            print(f"[⚠️] Реферал с user_id={ref_by} не найден в базе.")

    user_dict = model_to_dict(user)
    user_dict["referred_by"] = user.referred_by.user if user.referred_by else None

    return user_dict

@catch_error("ERR_GET_USER_LANGUAGE")
def get_user_language(user_id: int) -> str:
    try:
        user = models.TgUsers.objects.get(user=user_id)
        return user.language
    except models.TgUsers.DoesNotExist:
        return "ru"

@catch_error("ERR_SET_USER_LANGUAGE")
def set_user_language(user_id: int, language: str) -> dict:
    user = models.TgUsers.objects.get(user=user_id)
    user.language = language
    user.save()
    return model_to_dict(user)

@catch_error("ERR_CREATE_SCRIPT")
def create_script(user_id: int, start_at: datetime, stop_at: datetime = None) -> dict:
    if stop_at is None:
        stop_at =  start_at + timedelta(hours=2)

    # def_get_referrals = models.Referral.objects.filter(inviter=user_id, used=False)
    # if def_get_referrals.exists():
    #     referral = def_get_referrals.first()
    #     referral.used = True
    #     referral.save()

    script = models.IdScript.objects.create(
        owner=models.TgUsers.objects.get(user=user_id),
        start_at=start_at,
        stop_at=stop_at,
    )

    data = model_to_dict(script, fields=[
        'id', 'script', 'key', 'script_type', 'fingerprint',
        'start_at', 'stop_at', 'is_active', 'used',
        'max_usage', 'first_activate', 'first_seen'
    ])
    data['owner_id'] = script.owner_id
    return data


@catch_error("ERR_CREATE_TESTING_SCRIPT")
def create_testing_script(script_name: str) -> dict:
    user_id = 123456
    start_at = datetime.now()
    stop_at = start_at + timedelta(days=2)

    owner, _ = models.TgUsers.objects.get_or_create(user=user_id)

    script = models.IdScript.objects.create(
        owner=owner,
        script=script_name,
        start_at=start_at,
        stop_at=stop_at,
        is_active=True,
        max_usage=5
    )

    data = model_to_dict(script, fields=[
        'id', 'script', 'key', 'script_type', 'fingerprint',
        'start_at', 'stop_at', 'is_active', 'used',
        'max_usage', 'first_activate', 'first_seen'
    ])
    data['owner_id'] = script.owner_id
    data['created'] = True

    return data


@catch_error("ERR_ADD_TO_REFERRAL")
def add_to_referral(inviter_user_id: int, invited_user_id: int) -> dict:
    inviter = models.TgUsers.objects.get(user=inviter_user_id)
    invited = models.TgUsers.objects.get(user=invited_user_id)

    ref = models.Referral.objects.create(inviter=inviter, invited=invited)

    data = model_to_dict(ref, fields=['id', 'used', 'created_at'])
    data['inviter_user_id'] = inviter.user
    data['invited_user_id'] = invited.user
    return data


@catch_error("ERR_CHANGE_SCRIPT_STATUS")
def change_script_status(key, is_active: bool) -> dict:
    script = models.IdScript.objects.get(key=key)
    script.is_active = is_active
    script.save()
    data = model_to_dict(script, fields=[
        'id', 'script', 'key', 'script_type', 'fingerprint',
        'start_at', 'stop_at', 'is_active', 'used',
        'max_usage', 'first_activate', 'first_seen'
    ])
    data['owner_id'] = script.owner_id
    return data


@catch_error("ERR_GET_MY_SCRIPTS")
def get_my_scripts(user_id: int) -> list:
    scripts = models.IdScript.objects.filter(owner__user=user_id).order_by('-created_at')
    result = []
    for script in scripts:
        data = model_to_dict(script, fields=[
            'id', 'script', 'key', 'script_type', 'fingerprint',
            'start_at', 'stop_at', 'is_active', 'used',
            'max_usage', 'first_activate', 'first_seen'
        ])

        for field in ['start_at', 'stop_at', 'first_activate', 'first_seen']:
            if isinstance(data.get(field), datetime):
                data[field] = data[field].isoformat(sep=' ', timespec='seconds')

        result.append(data)

    return result


@catch_error("ERR_GET_MY_SCRIPTS_WITH_PAGINATION")
def get_my_scripts_with_pagination(user_id: int, page: int = 1, per_page: int = 5) -> dict:
    offset = (page - 1) * per_page
    queryset = models.IdScript.objects.filter(owner__user=user_id).order_by("-created_at")
    total = queryset.count()
    scripts = queryset[offset:offset + per_page]

    script_list = [
        model_to_dict(script, fields=[
            'id', 'script', 'key', 'script_type', 'fingerprint',
            'start_at', 'stop_at', 'is_active', 'used',
            'max_usage', 'first_activate', 'first_seen'
        ]) for script in scripts
    ]

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "scripts": script_list
    }


# Operations functions
@catch_error("ERR_GET_MY_SCRIPTS_WITH_PAGINATION")
def get_my_scripts_with_pagination(user_id: int, page: int = 1, per_page: int = 5) -> dict:
    offset = (page - 1) * per_page
    queryset = models.IdScript.objects.filter(owner__user=user_id).order_by("-created_at")
    total = queryset.count()
    scripts = queryset[offset:offset + per_page]

    script_list = [
        model_to_dict(script, fields=[
            'id', 'script', 'key', 'script_type', 'fingerprint',
            'start_at', 'stop_at', 'is_active', 'used',
            'max_usage', 'first_activate', 'first_seen'
        ]) for script in scripts
    ]

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "scripts": script_list
    }

@catch_error("ERR_GET_SCRIPT_BY_ID")
def get_script_by_id(script_id: int) -> dict:
    try:
        script = models.IdScript.objects.get(id=script_id)
        return model_to_dict(script, fields=[
            'id', 'script', 'key', 'script_type', 'fingerprint',
            'start_at', 'stop_at', 'is_active', 'used',
            'max_usage', 'first_activate', 'first_seen'
        ])
    except models.IdScript.DoesNotExist:
        return

@catch_error("ERR_GET_SCRIPT_BY_KEY")
def get_script_by_key(script: str) -> dict:
    try:
        script = models.IdScript.objects.get(key=script)
        return model_to_dict(script, fields=[
            'id', 'script', 'key', 'script_type', 'fingerprint',
            'start_at', 'stop_at', 'is_active', 'used',
            'max_usage', 'first_activate', 'first_seen'
        ])
    except models.IdScript.DoesNotExist:
        return


@catch_error("ERR_UPDATE_SCRIPT_TIME")
def update_script_time(key: str, start_at: datetime, stop_at: datetime) -> dict | None:
    try:
        script = models.IdScript.objects.get(key=key)

        if not script.is_active:
            return

        if script.fingerprint:
            return

        script.start_at = start_at
        script.stop_at = stop_at
        script.save()

        return model_to_dict(script, fields=[
            'id', 'script', 'key', 'script_type', 'fingerprint',
            'start_at', 'stop_at', 'is_active', 'used',
            'max_usage', 'first_activate', 'first_seen'
        ])

    except models.IdScript.DoesNotExist:
        return


@catch_error("ERR_GET_REFERRALS_COUNTS")
def get_referrals_counts(user_id: int) -> dict:
    referrals = models.Referral.objects.filter(inviter__user=user_id)
    all_referrals = [
        model_to_dict(ref, fields=['id', 'inviter', 'invited', 'used', 'created_at']) for ref in referrals
    ]
    used_referrals = [
        model_to_dict(ref, fields=['id', 'inviter', 'invited', 'used', 'created_at']) for ref in referrals if ref.used
    ]
    unused_referrals = [
        model_to_dict(ref, fields=['id', 'inviter', 'invited', 'used', 'created_at']) for ref in referrals if not ref.used
    ]
    return {
        "all": all_referrals,
        "used": used_referrals,
        "unused": unused_referrals,
    }


@catch_error("ERR_CHANGE_STATUS_REFERRALS")
def change_status_referral_by_id(referral_id: int, status: bool) -> dict | None:
    try:
        ref = models.Referral.objects.get(id=referral_id)
    except models.Referral.DoesNotExist:
        return None

    ref.used = status
    ref.save()

    return model_to_dict(ref, fields=['inviter', 'invited', 'used', 'created_at'])


@catch_error("ERR_GET_REFERRAL_INVITERS")
def get_referrals_inviters(user_id: int) -> list[dict]:
    users = models.TgUsers.objects.filter(referred_by__user=user_id)
    return [model_to_dict(user, fields=['user', 'is_admin', 'username', 'referred_by']) for user in users]

@catch_error("ERR_IS_ADMIN")
def is_admin(user_id: int) -> bool:
    return models.TgUsers.objects.filter(user=user_id, is_admin=True).exists()


@catch_error("ERR_GET_ADMINS")
def get_admins() -> list[dict]:
    return [
        model_to_dict(admin, fields=["user", "is_admin"])
        for admin in models.TgUsers.objects.filter(is_admin=True)
    ]


@catch_error("ERR_POLICE_UPDATE")
def set_police(user_id, police: bool) -> dict:
    user = models.TgUsers.objects.get(user=user_id)

    user.police = police
    user.save()

    return model_to_dict(user)


@catch_error("ERR_CHECK_ADMIN_CALLBACK")
def check_admin(user_id: int) -> bool:
    return models.TgUsers.objects.filter(user=user_id, is_admin=True).exists()
