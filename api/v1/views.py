import base64
import time

from django.views import View
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.core.serializers import serialize
from rest_framework import views, generics, status
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from datetime import timedelta

from django.conf import settings

from services.image2answer.model1_openai import base64_image_answer_question
from services.image2answer.model2_openai import solve_image_with_assistant
from services.image2answer.model3_openai import base64_image_answer_question as ai_model_v3
from services.image2answer.model4_openai_gpt5 import solve_task as ai_model_v4
from services.image2answer.model5_fastest_model_gpt5 import solve_task as ai_model_v5
from . import models, serializers, mixins
from . scripts import BASE_SCRIPT_PROD_UUID, BASE_SCRIPT
from . import permissions

class CreateIdScriptApiView(mixins.SuccessErrorResponseMixin, generics.ListCreateAPIView):
    queryset = models.IdScript.objects.all()
    serializer_class = serializers.CreateScriptSerializer

    permission_classes = [permissions.TokenPermission]

    def http_method_not_allowed(self, request, *args, **kwargs):
        return HttpResponseServerError()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return self.success(serializer.data)

class GetOrCreateTgUserView(mixins.SuccessErrorResponseMixin, views.APIView):
    permission_classes = [permissions.TokenPermission]

    def http_method_not_allowed(self, request, *args, **kwargs):
        return HttpResponseServerError()

    def post(self, request, *args, **kwargs):
        instance, created = models.TgUsers.objects.get_or_create(defaults=request.data)
        serializer = serializers.TgUserSerializer(instance)
        return self.success(serializer.data, status_code=201 if created else 200)

    def get(self, request, *args, **kwargs):
        users = models.TgUsers.objects.all()
        serializer = serializers.TgUserSerializer(users, many=True)
        return self.success(serializer.data)


class GetMyScriptsView(mixins.SuccessErrorResponseMixin, generics.ListAPIView):
    serializer_class = serializers.GetMyScriptsSerializer
    permission_classes = [permissions.TokenPermission]

    def http_method_not_allowed(self, request, *args, **kwargs):
        return HttpResponseServerError()

    def get_queryset(self):
        return models.IdScript.objects.filter(owner__user=self.request.query_params.get('user'))

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return self.success(serializer.data)


class ChangeIsActivateView(mixins.SuccessErrorResponseMixin, generics.UpdateAPIView):
    queryset = models.IdScript.objects.all()
    serializer_class = serializers.ChangeScriptISActiveSerializer
    lookup_field = 'key'
    permission_classes = [permissions.TokenPermission]

    def http_method_not_allowed(self, request, *args, **kwargs):
        return HttpResponseServerError()

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return self.success(response.data)


class ChangeScriptTimeView(mixins.SuccessErrorResponseMixin, views.APIView):
    permission_classes = [permissions.TokenPermission]

    def http_method_not_allowed(self, request, *args, **kwargs):
        return HttpResponseServerError()

    def put(self, request, *args, **kwargs):
        key = request.data.get("key")
        start_at_str = request.data.get("start_at")

        if not key:
            return self.error(
                code=3001,
                message="key not passed",
                details={"field": "key"},
                status_code=400
            )

        if not start_at_str:
            return self.error(
                code=2001,
                message="start_at not passed",
                details={"field": "start_at"},
                status_code=400
            )

        start_at = parse_datetime(start_at_str)
        if not start_at:
            return self.error(
                code=2002,
                message="start_at is not valid datetime format",
                details={"value": start_at_str},
                status_code=400
            )

        try:
            script = models.IdScript.objects.get(key=key)
        except models.IdScript.DoesNotExist:
            return self.error(
                code=3000,
                message="Script not found",
                details={"key": key},
                status_code=404
            )

        script.start_at = start_at
        script.stop_at = start_at + timedelta(hours=2)
        script.save()

        serializer = serializers.ChangeScriptISActiveSerializer(script)
        return self.success(data=serializer.data)


class AiAnswerCheckView(mixins.SuccessErrorResponseMixin, views.APIView):
    def get_image_base64(self, image_file):
        image_file.seek(0)
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
        image_file.seek(0)
        return encoded

    def http_method_not_allowed(self, request, *args, **kwargs):
        return HttpResponseServerError()

    def post(self, request, *args, **kwargs):
        serializer = serializers.AiAnswerSerializer(data=request.data)

        if not serializer.is_valid():
            return self.error("validation_error", "Validation error", serializer.errors)

        key = serializer.validated_data.get('key', None)
        fingerprint = serializer.validated_data.get('fingerprint', None)
        image = serializer.validated_data.get('image', None)

        try:
            script = models.IdScript.objects.get(key=key)
        except models.IdScript.DoesNotExist:
            return self.error("script_not_found", "Script not found", status_code=404)

        if not script.is_within_active_time():
            return self.error("inactive_script", "Script is not active or not in allowed time range")

        if script.is_max_usage_reached:
            return self.error("max_usage_reached", "Maximum usage reached for this script")

        script.initialize_activation_if_needed()

        if fingerprint:
            if script.fingerprint:
                if not script.is_fingerprint_valid(fingerprint):
                    return self.error("invalid_fingerprint", "Fingerprint mismatch", status_code=403)
            else:
                if script.is_ready_to_assign_fingerprint():
                    if not script.assign_fingerprint_if_unset(fingerprint):
                        return self.error("fingerprint_bind_error", "Failed to bind fingerprint", status_code=400)
                script.refresh_from_db()

        base64_img = self.get_image_base64(image)
        # data = ai_model_v3(base64_img)
        # data = solve_image_with_assistant(base64_img)
        #data = ai_model_v4(base64_img)
        data = ai_model_v5(base64_img)
        # from services.image2answer.model6_claude import solve_task as ai_model_v6_claude
        # data = ai_model_v6_claude(base64_img)
        if not data or not data.get("answer"):
            return self.error("parse_error", "Answer not found", status_code=404)

        script.increment_usage()

        answer = models.Answer.objects.create(
            script=script,
            image=image,
            answer=data
        )
        return self.success(data=data, status_code=201)


class GetScript(View):
    def script_filter(self, script_type, key, fingerprint):
        template = {
            "base_prod_uuid": BASE_SCRIPT_PROD_UUID,
            "base_uuid": BASE_SCRIPT
        }.get(script_type, BASE_SCRIPT)
        return template.format(key=key, domain=settings.DOMAIN, fingerprint=fingerprint)

    def get(self, request, script):
        if not script:
            return HttpResponseServerError()
        try:
            script_info = models.IdScript.objects.get(script=script)

            if not script_info.is_within_active_time():
                return HttpResponseServerError()

            if script_info.is_max_usage_reached:
                return HttpResponseServerError()

            content = self.script_filter(script_info.script_type, script_info.key, script_info.fingerprint)
            return HttpResponse(content, content_type='application/javascript')

        except Exception as e:
            return HttpResponseServerError()





