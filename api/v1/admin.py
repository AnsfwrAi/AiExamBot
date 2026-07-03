APP_NAME = 'v1'

from django.contrib import admin
from django.db.models.functions import TruncDate, TruncHour, ExtractHour
from django.db.models import Count, Sum, Avg, Q, F, Max, Min
from django.utils.html import format_html, mark_safe
from django.urls import reverse, path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django.template.response import TemplateResponse
from django.utils.timezone import now
from django.contrib import messages
from django.core.paginator import Paginator
from datetime import timedelta, datetime
import json
import csv
from django.contrib.admin import AdminSite
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Count, Sum, Avg
from datetime import datetime, timedelta

from .models import TgUsers, IdScript, Answer, Referral


class ActiveScriptFilter(admin.SimpleListFilter):
    title = 'Статус активности'
    parameter_name = 'activity_status'

    def lookups(self, request, model_admin):
        return (
            ('active_now', 'Активные сейчас'),
            ('expired', 'Истекшие'),
            ('not_started', 'Еще не начались'),
            ('max_usage_reached', 'Лимит использований'),
            ('low_usage', 'Мало использований (<10)'),
        )

    def queryset(self, request, queryset):
        current_time = now()
        if self.value() == 'active_now':
            return queryset.filter(
                is_active=True,
                start_at__lte=current_time,
                stop_at__gte=current_time,
                used__lt=F('max_usage')
            )
        elif self.value() == 'expired':
            return queryset.filter(stop_at__lt=current_time)
        elif self.value() == 'not_started':
            return queryset.filter(start_at__gt=current_time)
        elif self.value() == 'max_usage_reached':
            return queryset.filter(used__gte=F('max_usage'))
        elif self.value() == 'low_usage':
            return queryset.filter(used__lt=10)


class UsageRangeFilter(admin.SimpleListFilter):
    title = 'Диапазон использований'
    parameter_name = 'usage_range'

    def lookups(self, request, model_admin):
        return (
            ('0-10', '0-10 использований'),
            ('11-25', '11-25 использований'),
            ('26-50', '26-50 использований'),
            ('51-75', '51-75 использований'),
            ('75+', '75+ использований'),
        )

    def queryset(self, request, queryset):
        if self.value() == '0-10':
            return queryset.filter(used__range=(0, 10))
        elif self.value() == '11-25':
            return queryset.filter(used__range=(11, 25))
        elif self.value() == '26-50':
            return queryset.filter(used__range=(26, 50))
        elif self.value() == '51-75':
            return queryset.filter(used__range=(51, 75))
        elif self.value() == '75+':
            return queryset.filter(used__gte=75)


class ReferralCountFilter(admin.SimpleListFilter):
    title = 'Количество рефералов'
    parameter_name = 'referral_count'

    def lookups(self, request, model_admin):
        return (
            ('0', 'Без рефералов'),
            ('1-5', '1-5 рефералов'),
            ('6-10', '6-10 рефералов'),
            ('10+', '10+ рефералов'),
            ('top_referrers', 'Топ реферреры'),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.annotate(ref_count=Count('referred_users')).filter(ref_count=0)
        elif self.value() == '1-5':
            return queryset.annotate(ref_count=Count('referred_users')).filter(ref_count__range=(1, 5))
        elif self.value() == '6-10':
            return queryset.annotate(ref_count=Count('referred_users')).filter(ref_count__range=(6, 10))
        elif self.value() == '10+':
            return queryset.annotate(ref_count=Count('referred_users')).filter(ref_count__gte=10)
        elif self.value() == 'top_referrers':
            return queryset.annotate(ref_count=Count('referred_users')).filter(ref_count__gte=5).order_by('-ref_count')


@admin.register(TgUsers)
class TgUsersAdmin(admin.ModelAdmin):
    list_display = [
        'user_display', 'username', 'is_admin', 'referral_count_display',
        'scripts_count_display', 'total_usage_display', 'registration_date',
        'last_activity', 'referrer_display', 'admin_actions', 'police'
    ]
    list_filter = [
        'is_admin', 'created_at', ReferralCountFilter,
        ('referred_by', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['user', 'username', 'referred_by__username']
    readonly_fields = ['created_at', 'updated_at', 'referral_stats', 'user_activity_chart']
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'username', 'is_admin', 'police')
        }),
        ('Реферальная система', {
            'fields': ('referred_by', 'referral_stats'),
            'classes': ('collapse',)
        }),
        ('Статистика активности', {
            'fields': ('user_activity_chart',),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'make_admin', 'remove_admin', 'export_user_stats',
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('referred_by').prefetch_related(
            'referred_users', 'scripts', 'scripts__answers'
        ).annotate(
            ref_count=Count('referred_users'),
            scripts_count=Count('scripts'),
            total_script_usage=Sum('scripts__used')
        )

    def user_display(self, obj):
        color = '#28a745' if obj.is_admin else '#007bff'
        icon = '👑' if obj.is_admin else '👤'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.user
        )

    user_display.short_description = 'Пользователь'
    user_display.admin_order_field = 'user'

    def referral_count_display(self, obj):
        count = obj.ref_count
        if count == 0:
            return format_html('<span style="color: #6c757d;">0</span>')
        elif count <= 5:
            return format_html('<span style="color: #28a745;">📈 {}</span>', count)
        else:
            return format_html('<span style="color: #dc3545; font-weight: bold;">🔥 {}</span>', count)

    referral_count_display.short_description = 'Рефералы'
    referral_count_display.admin_order_field = 'ref_count'

    def scripts_count_display(self, obj):
        count = obj.scripts_count
        if count == 0:
            return format_html('<span style="color: #6c757d;">0</span>')
        return format_html('<span style="color: #17a2b8;">📜 {}</span>', count)

    scripts_count_display.short_description = 'Скрипты'
    scripts_count_display.admin_order_field = 'scripts_count'

    def total_usage_display(self, obj):
        usage = obj.total_script_usage or 0
        if usage == 0:
            return format_html('<span style="color: #6c757d;">0</span>')
        elif usage <= 50:
            return format_html('<span style="color: #28a745;">⚡ {}</span>', usage)
        else:
            return format_html('<span style="color: #dc3545; font-weight: bold;">🚀 {}</span>', usage)

    total_usage_display.short_description = 'Общее использование'
    total_usage_display.admin_order_field = 'total_script_usage'

    def registration_date(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')

    registration_date.short_description = 'Регистрация'
    registration_date.admin_order_field = 'created_at'

    def last_activity(self, obj):
        return obj.updated_at.strftime('%d.%m.%Y %H:%M')

    last_activity.short_description = 'Последняя активность'
    last_activity.admin_order_field = 'updated_at'

    def referrer_display(self, obj):
        if obj.referred_by:
            url = reverse(f'admin:{APP_NAME}_tgusers_change', args=[obj.referred_by.id])
            return format_html('<a href="{}" style="color: #007bff;">👥 {}</a>',
                               url, obj.referred_by.username or f"ID:{obj.referred_by.user}")
        return format_html('<span style="color: #6c757d;">Прямая регистрация</span>')

    referrer_display.short_description = 'Пригласил'

    def admin_actions(self, obj):
        buttons = []

        if obj.scripts_count > 0:
            scripts_url = f"{reverse(f'admin:{APP_NAME}_idscript_changelist')}?owner__id__exact={obj.id}"
            buttons.append(f'<a href="{scripts_url}" class="button" style="margin-right: 5px;">📜 Скрипты</a>')

        stats_url = reverse('admin:user_detailed_stats', args=[obj.id])
        buttons.append(f'<a href="{stats_url}" class="button" style="margin-right: 5px;">📊 Статистика</a>')

        return format_html(''.join(buttons))

    admin_actions.short_description = 'Действия'

    def referral_stats(self, obj):
        if obj.pk:
            referred = obj.referred_users.all()
            if not referred:
                return "Нет рефералов"

            stats = f"<strong>Всего рефералов:</strong> {len(referred)}<br>"
            stats += "<strong>Список рефералов:</strong><br>"
            for user in referred[:10]:
                stats += f"• {user.username or f'ID:{user.user}'} (рег. {user.created_at.strftime('%d.%m.%Y')})<br>"

            if len(referred) > 10:
                stats += f"... и еще {len(referred) - 10} пользователей"

            return mark_safe(stats)
        return "Сохраните пользователя, чтобы увидеть статистику"

    referral_stats.short_description = 'Реферальная статистика'

    def user_activity_chart(self, obj):
        if obj.pk:
            return mark_safe(f"""
                <div id="user-activity-{obj.pk}" style="height: 300px; border: 1px solid #ddd; padding: 10px;">
                    <h4>График активности пользователя</h4>
                    <p>Скрипты: {obj.scripts_count}</p>
                    <p>Общее использование: {obj.total_script_usage or 0}</p>
                    <p>Рефералы: {obj.ref_count}</p>
                </div>
            """)
        return "Сохраните пользователя, чтобы увидеть график"

    user_activity_chart.short_description = 'График активности'

    def make_admin(self, request, queryset):
        updated = queryset.update(is_admin=True)
        self.message_user(request, f'{updated} пользователей назначены администраторами.')

    make_admin.short_description = 'Назначить администраторами'

    def remove_admin(self, request, queryset):
        updated = queryset.update(is_admin=False)
        self.message_user(request, f'{updated} пользователей лишены прав администратора.')

    remove_admin.short_description = 'Убрать права администратора'

    def export_user_stats(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_stats.csv"'

        writer = csv.writer(response)
        writer.writerow(['User ID', 'Username', 'Is Admin', 'Referrals', 'Scripts', 'Total Usage', 'Registration'])

        for user in queryset:
            writer.writerow([
                user.user, user.username, user.is_admin,
                user.ref_count, user.scripts_count,
                user.total_script_usage or 0,
                user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response

    export_user_stats.short_description = 'Экспорт статистики в CSV'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('stats/<int:user_id>/', self.admin_site.admin_view(self.user_detailed_stats),
                 name='user_detailed_stats'),
            path('analytics/', self.admin_site.admin_view(self.analytics_dashboard),
                 name='users_analytics'),
        ]
        return custom_urls + urls

    def user_detailed_stats(self, request, user_id):
        tg_user = get_object_or_404(TgUsers, pk=user_id)

        scripts = tg_user.scripts.all().annotate(
            answers_count=Count('answers')
        ).order_by('-created_at')

        referrals = tg_user.referred_users.all().order_by('-created_at')

        context = {
            'tg_user': tg_user,
            'scripts': scripts,
            'referrals': referrals,
            'total_answers': sum(s.answers_count for s in scripts),
            'active_scripts': scripts.filter(is_active=True).count(),
            'title': f'Детальная статистика: {tg_user.username or f"ID:{tg_user.user}"}',
        }

        return TemplateResponse(request, 'admin/user_detailed_stats.html', context)

    def analytics_dashboard(self, request):
        total_users = TgUsers.objects.count()
        admin_users = TgUsers.objects.filter(is_admin=True).count()

        users_with_referrals = TgUsers.objects.annotate(
            ref_count=Count('referred_users')
        ).filter(ref_count__gt=0)

        top_referrers = users_with_referrals.order_by('-ref_count')[:10]

        thirty_days_ago = now() - timedelta(days=30)
        daily_registrations = TgUsers.objects.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        context = {
            'total_users': total_users,
            'admin_users': admin_users,
            'regular_users': total_users - admin_users,
            'top_referrers': top_referrers,
            'daily_registrations': list(daily_registrations),
            'users_with_referrals_count': users_with_referrals.count(),
            'title': 'Аналитика пользователей',
        }

        return TemplateResponse(request, 'admin/users_analytics.html', context)




@admin.register(IdScript)
class IdScriptAdmin(admin.ModelAdmin):
    list_display = [
        'script_display', 'owner_display', 'status_display', 'usage_progress',
        'script_type', 'fingerprint_status', 'time_remaining', 'answers_count',
        'created_display', 'admin_actions'
    ]
    list_filter = [
        ActiveScriptFilter, UsageRangeFilter, 'script_type', 'is_active',
        'created_at', 'start_at', 'stop_at',
        ('owner', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['script', 'key', 'owner__username', 'owner__user', 'fingerprint']
    readonly_fields = [
        'key', 'created_at', 'updated_at', 'first_activate',
        'first_seen', 'usage_analytics', 'time_analytics'
    ]

    fieldsets = (
        ('Основная информация', {
            'fields': ('script', 'key', 'owner', 'script_type')
        }),
        ('Настройки активности', {
            'fields': ('is_active', 'start_at', 'stop_at', 'max_usage')
        }),
        ('Использование и безопасность', {
            'fields': ('used', 'fingerprint', 'first_activate', 'first_seen'),
            'classes': ('collapse',)
        }),
        ('Аналитика', {
            'fields': ('usage_analytics', 'time_analytics'),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'activate_scripts', 'deactivate_scripts', 'reset_usage',
        'extend_time', 'export_scripts', 'clone_scripts'
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner').prefetch_related(
            'answers'
        ).annotate(
            answers_count=Count('answers')
        )

    def script_display(self, obj):
        status_color = '#28a745' if obj.is_within_active_time() else '#dc3545'
        icon = '🟢' if obj.is_within_active_time() else '🔴'
        return format_html(
            '<span style="color: {};">{} <strong>{}</strong></span><br>'
            '<small style="color: #6c757d;">Key: {}...</small>',
            status_color, icon, obj.script, obj.key[:8]
        )

    script_display.short_description = 'Скрипт'
    script_display.admin_order_field = 'script'

    def owner_display(self, obj):
        url = reverse(f'admin:{APP_NAME}_tgusers_change', args=[obj.owner.id])
        return format_html(
            '<a href="{}" style="color: #007bff;">👤 {}</a>',
            url, obj.owner.username or f"ID:{obj.owner.user}"
        )

    owner_display.short_description = 'Владелец'
    owner_display.admin_order_field = 'owner__user'

    def status_display(self, obj):
        current_time = now()

        if not obj.is_active:
            return format_html('<span style="color: #6c757d;">⏸️ Неактивен</span>')
        elif obj.start_at > current_time:
            return format_html('<span style="color: #ffc107;">⏳ Ожидает старта</span>')
        elif obj.stop_at < current_time:
            return format_html('<span style="color: #dc3545;">⏰ Истек</span>')
        elif obj.used >= obj.max_usage:
            return format_html('<span style="color: #dc3545;">🚫 Лимит достигнут</span>')
        else:
            return format_html('<span style="color: #28a745;">✅ Активен</span>')

    status_display.short_description = 'Статус'

    def usage_progress(self, obj):
        percentage = (obj.used / obj.max_usage) * 100 if obj.max_usage > 0 else 0

        if percentage <= 50:
            color = '#28a745'
        elif percentage <= 80:
            color = '#ffc107'
        else:
            color = '#dc3545'

        return format_html(
            '<div style="background: #e9ecef; border-radius: 4px; overflow: hidden; width: 100px;">'
            '<div style="background: {}; height: 20px; width: {}%; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}/{}'
            '</div></div>',
            color, percentage, obj.used, obj.max_usage
        )

    usage_progress.short_description = 'Использование'

    def fingerprint_status(self, obj):
        if obj.fingerprint:
            return format_html('<span style="color: #28a745;">🔒 Привязан</span>')
        else:
            return format_html('<span style="color: #ffc107;">🔓 Не привязан</span>')

    fingerprint_status.short_description = 'Отпечаток'

    def time_remaining(self, obj):
        if not obj.is_active:
            return format_html('<span style="color: #6c757d;">—</span>')

        current_time = now()
        if obj.stop_at <= current_time:
            return format_html('<span style="color: #dc3545;">Истек</span>')

        remaining = obj.stop_at - current_time
        days = remaining.days
        hours = remaining.seconds // 3600

        if days > 0:
            return format_html('<span style="color: #28a745;">{} дн. {} ч.</span>', days, hours)
        elif hours > 0:
            return format_html('<span style="color: #ffc107;">{} ч.</span>', hours)
        else:
            minutes = (remaining.seconds % 3600) // 60
            return format_html('<span style="color: #dc3545;">{} мин.</span>', minutes)

    time_remaining.short_description = 'Осталось времени'

    def answers_count(self, obj):
        count = obj.answers_count
        if count == 0:
            return format_html('<span style="color: #6c757d;">0</span>')
        return format_html('<span style="color: #17a2b8;">📋 {}</span>', count)

    answers_count.short_description = 'Ответы'
    answers_count.admin_order_field = 'answers_count'

    def created_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')

    created_display.short_description = 'Создан'
    created_display.admin_order_field = 'created_at'

    def admin_actions(self, obj):
        buttons = []

        if obj.answers_count > 0:
            answers_url = f"{reverse(f'admin:{APP_NAME}_answer_changelist')}?script__id__exact={obj.id}"
            buttons.append(f'<a href="{answers_url}" class="button" style="margin-right: 5px;">📋 Ответы</a>')

        clone_url = reverse('admin:clone_script', args=[obj.id])
        buttons.append(f'<a href="{clone_url}" class="button" style="margin-right: 5px;">📋 Клон</a>')

        return format_html(''.join(buttons))

    admin_actions.short_description = 'Действия'

    def usage_analytics(self, obj):
        if obj.pk:
            answers = obj.answers.all().order_by('created_at')
            if not answers:
                return "Нет данных об использовании"

            usage_by_day = {}
            for answer in answers:
                day = answer.created_at.date()
                usage_by_day[day] = usage_by_day.get(day, 0) + 1

            stats = f"<strong>Всего ответов:</strong> {len(answers)}<br>"
            stats += f"<strong>Первое использование:</strong> {answers[0].created_at.strftime('%d.%m.%Y %H:%M')}<br>"
            stats += f"<strong>Последнее использование:</strong> {answers.last().created_at.strftime('%d.%m.%Y %H:%M')}<br>"
            stats += "<strong>Использование по дням:</strong><br>"

            for day, count in sorted(usage_by_day.items(), reverse=True)[:7]:
                stats += f"• {day.strftime('%d.%m.%Y')}: {count} раз<br>"

            return mark_safe(stats)
        return "Сохраните скрипт, чтобы увидеть аналитику"

    usage_analytics.short_description = 'Аналитика использования'

    def time_analytics(self, obj):
        if obj.pk:
            current_time = now()
            total_duration = obj.stop_at - obj.start_at

            if current_time < obj.start_at:
                time_to_start = obj.start_at - current_time
                stats = f"<strong>До старта:</strong> {time_to_start}<br>"
            elif current_time > obj.stop_at:
                expired_time = current_time - obj.stop_at
                stats = f"<strong>Истек:</strong> {expired_time} назад<br>"
            else:
                elapsed = current_time - obj.start_at
                remaining = obj.stop_at - current_time
                progress = (elapsed.total_seconds() / total_duration.total_seconds()) * 100

                stats = f"<strong>Прошло времени:</strong> {elapsed}<br>"
                stats += f"<strong>Осталось времени:</strong> {remaining}<br>"
                stats += f"<strong>Прогресс:</strong> {progress:.1f}%<br>"

            stats += f"<strong>Общая продолжительность:</strong> {total_duration}<br>"

            if obj.first_activate:
                activation_delay = obj.first_activate - obj.start_at
                stats += f"<strong>Задержка активации:</strong> {activation_delay}<br>"

            return mark_safe(stats)
        return "Сохраните скрипт, чтобы увидеть временную аналитику"

    time_analytics.short_description = 'Временная аналитика'

    def activate_scripts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} скриптов активировано.')

    activate_scripts.short_description = 'Активировать скрипты'

    def deactivate_scripts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} скриптов деактивировано.')

    deactivate_scripts.short_description = 'Деактивировать скрипты'

    def reset_usage(self, request, queryset):
        updated = queryset.update(used=0)
        self.message_user(request, f'Сброшен счетчик использования для {updated} скриптов.')

    reset_usage.short_description = 'Сбросить счетчик использования'

    def extend_time(self, request, queryset):
        for script in queryset:
            script.stop_at = script.stop_at + timedelta(hours=24)
            script.save()

        self.message_user(request, f'Время работы продлено на 24 часа для {queryset.count()} скриптов.')

    extend_time.short_description = 'Продлить время работы на 24ч'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('clone/<int:script_id>/', self.admin_site.admin_view(self.clone_script),
                 name='clone_script'),
            path('analytics/', self.admin_site.admin_view(self.scripts_analytics),
                 name='scripts_analytics'),
        ]
        return custom_urls + urls

    def clone_script(self, request, script_id):
        original = get_object_or_404(IdScript, pk=script_id)

        cloned = IdScript.objects.create(
            owner=original.owner,
            script_type=original.script_type,
            start_at=now(),
            stop_at=now() + timedelta(hours=24),
            is_active=False,
            max_usage=original.max_usage
        )

        messages.success(request, f'Скрипт {original.script} успешно клонирован как {cloned.script}')

        return redirect(reverse(f'admin:{APP_NAME}_idscript_change', args=[cloned.id]))

    def scripts_analytics(self, request):
        total_scripts = IdScript.objects.count()
        active_scripts = IdScript.objects.filter(is_active=True).count()

        current_time = now()
        active_now = IdScript.objects.filter(
            is_active=True,
            start_at__lte=current_time,
            stop_at__gte=current_time,
            used__lt=F('max_usage')
        ).count()

        script_types = IdScript.objects.values('script_type').annotate(
            count=Count('id'),
            avg_usage=Avg('used'),
            total_usage=Sum('used')
        ).order_by('-count')

        top_owners = TgUsers.objects.annotate(
            scripts_count=Count('scripts'),
            total_usage=Sum('scripts__used')
        ).filter(scripts_count__gt=0).order_by('-scripts_count')[:10]

        thirty_days_ago = now() - timedelta(days=30)
        daily_usage = Answer.objects.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        context = {
            'total_scripts': total_scripts,
            'active_scripts': active_scripts,
            'active_now': active_now,
            'inactive_scripts': total_scripts - active_scripts,
            'script_types': script_types,
            'top_owners': top_owners,
            'daily_usage': list(daily_usage),
            'title': 'Аналитика скриптов',
        }

        return TemplateResponse(request, 'admin/scripts_analytics.html', context)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'script_display', 'owner_display', 'image_preview',
        'answer_preview', 'created_display', 'admin_actions'
    ]
    list_filter = [
        'created_at',
        ('script', admin.RelatedOnlyFieldListFilter),
        ('script__owner', admin.RelatedOnlyFieldListFilter),
        ('script__script_type', admin.ChoicesFieldListFilter),
    ]
    search_fields = [
        'script__script', 'script__owner__username', 'script__owner__user',
        'answer', 'id'
    ]
    readonly_fields = ['created_at', 'updated_at', 'answer_details', 'image_info']

    fieldsets = (
        ('Основная информация', {
            'fields': ('script', 'image', 'answer')
        }),
        ('Детальная информация', {
            'fields': ('answer_details', 'image_info'),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['export_answers', 'delete_old_answers', 'analyze_answers']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'script', 'script__owner'
        )

    def script_display(self, obj):
        url = reverse(f'admin:{APP_NAME}_idscript_change', args=[obj.script.id])
        status_icon = '🟢' if obj.script.is_within_active_time() else '🔴'
        return format_html(
            '<a href="{}" style="color: #007bff;">{} {}</a>',
            url, status_icon, obj.script.script
        )

    script_display.short_description = 'Скрипт'
    script_display.admin_order_field = 'script__script'

    def owner_display(self, obj):
        url = reverse(f'admin:{APP_NAME}_tgusers_change', args=[obj.script.owner.id])
        return format_html(
            '<a href="{}" style="color: #007bff;">👤 {}</a>',
            url, obj.script.owner.username or f"ID:{obj.script.owner.user}"
        )

    owner_display.short_description = 'Владелец'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 4px;" />',
                obj.image.url
            )
        return format_html('<span style="color: #6c757d;">Нет изображения</span>')

    image_preview.short_description = 'Превью'

    def answer_preview(self, obj):
        if obj.answer:
            if isinstance(obj.answer, dict):
                preview = str(obj.answer)[:100]
                if len(str(obj.answer)) > 100:
                    preview += "..."
                return format_html(
                    '<div style="max-width: 200px; overflow: hidden; font-family: monospace; font-size: 12px;">{}</div>',
                    preview
                )
            return str(obj.answer)[:100] + ("..." if len(str(obj.answer)) > 100 else "")
        return format_html('<span style="color: #6c757d;">Нет ответа</span>')

    answer_preview.short_description = 'Ответ (превью)'

    def created_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M:%S')

    created_display.short_description = 'Создан'
    created_display.admin_order_field = 'created_at'

    def admin_actions(self, obj):
        buttons = []

        view_url = reverse('admin:view_answer_details', args=[obj.id])
        buttons.append(f'<a href="{view_url}" class="button" style="margin-right: 5px;">👁️ Детали</a>')

        if obj.image:
            buttons.append(
                f'<a href="{obj.image.url}" class="button" download style="margin-right: 5px;">💾 Скачать</a>')

        return format_html(''.join(buttons))

    admin_actions.short_description = 'Действия'

    def answer_details(self, obj):
        if obj.answer:
            if isinstance(obj.answer, dict):
                formatted_json = json.dumps(obj.answer, ensure_ascii=False, indent=2)
                return format_html(
                    '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; max-height: 300px; overflow-y: auto;">{}</pre>',
                    formatted_json
                )
            return str(obj.answer)
        return "Нет данных ответа"

    answer_details.short_description = 'Полный ответ'

    def image_info(self, obj):
        if obj.image:
            try:
                file_size = obj.image.size
                info = f"<strong>Размер файла:</strong> {file_size / 1024:.1f} KB<br>"
                info += f"<strong>Путь:</strong> {obj.image.name}<br>"
                return mark_safe(info)
            except Exception as e:
                return f"Ошибка получения информации: {str(e)}"
        return "Изображение отсутствует"

    image_info.short_description = 'Информация об изображении'

    def export_answers(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="answers.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Script', 'Owner', 'Answer', 'Image', 'Created'])

        for answer in queryset:
            writer.writerow([
                answer.id,
                answer.script.script,
                answer.script.owner.username or f"ID:{answer.script.owner.user}",
                str(answer.answer)[:500] if answer.answer else '',
                answer.image.url if answer.image else '',
                answer.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response

    export_answers.short_description = 'Экспорт ответов в CSV'

    def delete_old_answers(self, request, queryset):
        thirty_days_ago = now() - timedelta(days=30)
        old_answers = queryset.filter(created_at__lt=thirty_days_ago)
        count = old_answers.count()
        old_answers.delete()

        self.message_user(request, f'Удалено {count} старых ответов (старше 30 дней).')

    delete_old_answers.short_description = 'Удалить старые ответы (>30 дней)'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('details/<int:answer_id>/', self.admin_site.admin_view(self.view_answer_details),
                 name='view_answer_details'),
            path('analytics/', self.admin_site.admin_view(self.answers_analytics),
                 name='answers_analytics'),
        ]
        return custom_urls + urls

    def view_answer_details(self, request, answer_id):
        answer = get_object_or_404(Answer, pk=answer_id)

        context = {
            'answer': answer,
            'title': f'Детали ответа #{answer.id}',
        }

        return TemplateResponse(request, 'admin/answer_details.html', context)

    def answers_analytics(self, request):
        total_answers = Answer.objects.count()

        thirty_days_ago = now() - timedelta(days=30)
        daily_answers = Answer.objects.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        top_scripts = IdScript.objects.annotate(
            answers_count=Count('answers')
        ).filter(answers_count__gt=0).order_by('-answers_count')[:10]

        hourly_distribution = Answer.objects.annotate(
            hour=TruncHour('created_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')

        context = {
            'total_answers': total_answers,
            'daily_answers': list(daily_answers),
            'top_scripts': top_scripts,
            'hourly_distribution': list(hourly_distribution),
            'answers_today': Answer.objects.filter(
                created_at__date=now().date()
            ).count(),
            'title': 'Аналитика ответов',
        }

        return TemplateResponse(request, 'admin/answers_analytics.html', context)


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'inviter_display', 'invited_display', 'used_status',
        'created_display', 'admin_actions'
    ]
    list_filter = [
        'used', 'created_at',
        ('inviter', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'inviter__username', 'inviter__user',
        'invited__username', 'invited__user'
    ]
    readonly_fields = ['created_at', 'referral_stats']

    fieldsets = (
        ('Реферальная связь', {
            'fields': ('inviter', 'invited', 'used')
        }),
        ('Статистика', {
            'fields': ('referral_stats',),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_used', 'mark_as_unused', 'export_referrals']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('inviter', 'invited')

    def inviter_display(self, obj):
        url = reverse(f'admin:{APP_NAME}_tgusers_change', args=[obj.inviter.id])
        icon = '👑' if obj.inviter.is_admin else '👤'
        return format_html(
            '<a href="{}" style="color: #007bff;">{} {}</a>',
            url, icon, obj.inviter.username or f"ID:{obj.inviter.user}"
        )

    inviter_display.short_description = 'Пригласивший'
    inviter_display.admin_order_field = 'inviter__user'

    def invited_display(self, obj):
        url = reverse(f'admin:{APP_NAME}_tgusers_change', args=[obj.invited.id])
        icon = '👑' if obj.invited.is_admin else '👤'
        return format_html(
            '<a href="{}" style="color: #007bff;">{} {}</a>',
            url, icon, obj.invited.username or f"ID:{obj.invited.user}"
        )

    invited_display.short_description = 'Приглашенный'
    invited_display.admin_order_field = 'invited__user'

    def used_status(self, obj):
        if obj.used:
            return format_html('<span style="color: #28a745;">✅ Использован</span>')
        else:
            return format_html('<span style="color: #ffc107;">⏳ Не использован</span>')

    used_status.short_description = 'Статус'
    used_status.admin_order_field = 'used'

    def created_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')

    created_display.short_description = 'Создан'
    created_display.admin_order_field = 'created_at'

    def admin_actions(self, obj):
        buttons = []

        if obj.used:
            toggle_url = reverse('admin:toggle_referral_status', args=[obj.id])
            buttons.append(
                f'<a href="{toggle_url}" class="button" style="margin-right: 5px;">⏳ Сделать неиспользованным</a>')
        else:
            toggle_url = reverse('admin:toggle_referral_status', args=[obj.id])
            buttons.append(
                f'<a href="{toggle_url}" class="button" style="margin-right: 5px;">✅ Отметить использованным</a>')

        return format_html(''.join(buttons))

    admin_actions.short_description = 'Действия'

    def referral_stats(self, obj):
        if obj.pk:
            inviter_stats = obj.inviter.referred_users.count()
            invited_stats = obj.invited.scripts.count()

            stats = f"<strong>Статистика пригласившего:</strong><br>"
            stats += f"• Всего приглашений: {inviter_stats}<br>"
            stats += f"• Дата регистрации: {obj.inviter.created_at.strftime('%d.%m.%Y %H:%M')}<br><br>"

            stats += f"<strong>Статистика приглашенного:</strong><br>"
            stats += f"• Количество скриптов: {invited_stats}<br>"
            stats += f"• Дата регистрации: {obj.invited.created_at.strftime('%d.%m.%Y %H:%M')}<br>"

            time_diff = obj.invited.created_at - obj.created_at
            if time_diff.total_seconds() > 0:
                stats += f"• Время до регистрации: {time_diff}<br>"

            return mark_safe(stats)
        return "Сохраните реферал, чтобы увидеть статистику"

    referral_stats.short_description = 'Детальная статистика'

    def mark_as_used(self, request, queryset):
        updated = queryset.update(used=True)
        self.message_user(request, f'{updated} рефералов отмечены как использованные.')

    mark_as_used.short_description = 'Отметить как использованные'

    def mark_as_unused(self, request, queryset):
        updated = queryset.update(used=False)
        self.message_user(request, f'{updated} рефералов отмечены как неиспользованные.')

    mark_as_unused.short_description = 'Отметить как неиспользованные'

    def export_referrals(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="referrals.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Inviter', 'Invited', 'Used', 'Created'])

        for referral in queryset:
            writer.writerow([
                referral.id,
                referral.inviter.username or f"ID:{referral.inviter.user}",
                referral.invited.username or f"ID:{referral.invited.user}",
                'Да' if referral.used else 'Нет',
                referral.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response

    export_referrals.short_description = 'Экспорт рефералов в CSV'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('toggle/<int:referral_id>/', self.admin_site.admin_view(self.toggle_referral_status),
                 name='toggle_referral_status'),
            path('analytics/', self.admin_site.admin_view(self.referrals_analytics),
                 name='referrals_analytics'),
        ]
        return custom_urls + urls

    def toggle_referral_status(self, request, referral_id):
        referral = get_object_or_404(Referral, pk=referral_id)
        referral.used = not referral.used
        referral.save()

        status = 'использованным' if referral.used else 'неиспользованным'
        messages.success(request, f'Реферал #{referral.id} отмечен как {status}')

        return redirect(reverse(f'admin:{APP_NAME}_referral_changelist'))

    def referrals_analytics(self, request):
        total_referrals = Referral.objects.count()
        used_referrals = Referral.objects.filter(used=True).count()

        top_referrers = TgUsers.objects.annotate(
            referrals_count=Count('invited'),
            used_referrals_count=Count('invited', filter=Q(invited__used=True))
        ).filter(referrals_count__gt=0).order_by('-referrals_count')[:10]

        thirty_days_ago = now() - timedelta(days=30)
        daily_referrals = Referral.objects.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        conversion_rate = (used_referrals / total_referrals * 100) if total_referrals > 0 else 0

        context = {
            'total_referrals': total_referrals,
            'used_referrals': used_referrals,
            'unused_referrals': total_referrals - used_referrals,
            'conversion_rate': round(conversion_rate, 2),
            'top_referrers': top_referrers,
            'daily_referrals': list(daily_referrals),
            'referrals_today': Referral.objects.filter(
                created_at__date=now().date()
            ).count(),
            'title': 'Аналитика рефералов',
        }

        return TemplateResponse(request, 'admin/referrals_analytics.html', context)


class CustomAdminSite(AdminSite):
    site_header = "🚀 Управление скриптами"
    site_title = "Admin Panel"
    index_title = "Добро пожаловать в панель управления"

    def index(self, request, extra_context=None):
        total_users = TgUsers.objects.count()
        total_scripts = IdScript.objects.count()
        total_answers = Answer.objects.count()
        total_referrals = Referral.objects.count()

        active_scripts = IdScript.objects.filter(is_active=True).count()
        admin_users = TgUsers.objects.filter(is_admin=True).count()
        used_referrals = Referral.objects.filter(used=True).count()
        answers_today = Answer.objects.filter(created_at__date=datetime.now().date()).count()

        thirty_days_ago = datetime.now() - timedelta(days=30)

        daily_registrations = TgUsers.objects.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(count=Count('id')).order_by('day')

        daily_usage = Answer.objects.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(count=Count('id')).order_by('day')

        top_users = TgUsers.objects.annotate(
            scripts_count=Count('scripts'),
            total_usage=Sum('scripts__used'),
            referrals_count=Count('referred_users')
        ).filter(scripts_count__gt=0).order_by('-total_usage')[:5]

        top_scripts = IdScript.objects.annotate(
            answers_count=Count('answers')
        ).filter(answers_count__gt=0).order_by('-answers_count')[:5]

        script_types = IdScript.objects.values('script_type').annotate(
            count=Count('id'),
            avg_usage=Avg('used')
        ).order_by('-count')

        seven_days_ago = datetime.now() - timedelta(days=7)
        hourly_activity = Answer.objects.filter(
            created_at__gte=seven_days_ago
        ).annotate(
            hour=Extract('created_at', 'hour')
        ).values('hour').annotate(count=Count('id')).order_by('hour')

    site_header = "🚀 Управление скриптами"
    site_title = "Admin Panel"
    index_title = "Добро пожаловать в панель управления"

    def index(self, request, extra_context=None):
        total_users = TgUsers.objects.count()
        total_scripts = IdScript.objects.count()
        total_answers = Answer.objects.count()
        total_referrals = Referral.objects.count()

        active_scripts = IdScript.objects.filter(is_active=True).count()
        admin_users = TgUsers.objects.filter(is_admin=True).count()
        used_referrals = Referral.objects.filter(used=True).count()
        answers_today = Answer.objects.filter(created_at__date=datetime.now().date()).count()

        thirty_days_ago = datetime.now() - timedelta(days=30)

        daily_registrations = TgUsers.objects.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        daily_usage = Answer.objects.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        top_users = TgUsers.objects.annotate(
            scripts_count=Count('scripts'),
            total_usage=Sum('scripts__used'),
            referrals_count=Count('referred_users')
        ).filter(scripts_count__gt=0).order_by('-total_usage')[:5]

        top_scripts = IdScript.objects.annotate(
            answers_count=Count('answers')
        ).filter(answers_count__gt=0).order_by('-answers_count')[:5]

        script_types = IdScript.objects.values('script_type').annotate(
            count=Count('id'),
            avg_usage=Avg('used')
        ).order_by('-count')

        seven_days_ago = datetime.now() - timedelta(days=7)

        hourly_activity = Answer.objects.filter(
            created_at__gte=seven_days_ago
        ).annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')

        referral_conversion = (used_referrals / total_referrals * 100) if total_referrals > 0 else 0

        context = {}
        if extra_context:
            context.update(extra_context)

        context.update({
            'total_users': total_users,
            'total_scripts': total_scripts,
            'total_answers': total_answers,
            'total_referrals': total_referrals,

            'active_scripts': active_scripts,
            'admin_users': admin_users,
            'used_referrals': used_referrals,
            'answers_today': answers_today,

            'active_scripts_percent': round((active_scripts / total_scripts * 100) if total_scripts > 0 else 0, 1),
            'admin_percent': round((admin_users / total_users * 100) if total_users > 0 else 0, 1),
            'referral_conversion': round(referral_conversion, 1),

            'daily_registrations': list(daily_registrations),
            'daily_usage': list(daily_usage),
            'hourly_activity': list(hourly_activity),
            'script_types': list(script_types),

            'top_users': top_users,
            'top_scripts': top_scripts,

            'title': 'Главная панель',
            'has_permission': request.user.is_active and request.user.is_staff,
        })

        return TemplateResponse(request, "admin/dashboard.html", context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard-api/stats/', self.admin_view(self.dashboard_api), name='dashboard_api'),
        ]
        return custom_urls + urls

    def dashboard_api(self, request):
        stats = {
            'total_users': TgUsers.objects.count(),
            'active_scripts': IdScript.objects.filter(is_active=True).count(),
            'answers_today': Answer.objects.filter(created_at__date=datetime.now().date()).count(),
            'referrals_today': Referral.objects.filter(created_at__date=datetime.now().date()).count(),
        }
        return JsonResponse(stats)

custom_admin_site = CustomAdminSite(name='custom_admin')
custom_admin_site.register(TgUsers, TgUsersAdmin)
custom_admin_site.register(IdScript, IdScriptAdmin)
custom_admin_site.register(Answer, AnswerAdmin)
custom_admin_site.register(Referral, ReferralAdmin)
