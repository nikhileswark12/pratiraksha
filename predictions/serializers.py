from rest_framework import serializers
from django.utils import timezone


class PredictionRequestSerializer(serializers.Serializer):
    event = serializers.CharField(max_length=200, allow_blank=True, required=False, default="")
    pollution_level = serializers.FloatField(min_value=0, max_value=1000, required=False, default=50)
    temperature = serializers.FloatField(min_value=-50, max_value=70, required=False, default=25)
    humidity = serializers.FloatField(min_value=0, max_value=100, required=False, default=50)
    rainfall = serializers.FloatField(min_value=0, max_value=1000, required=False, default=0)
    city = serializers.CharField(max_length=100, allow_blank=False, required=False, default="Unknown")
    date = serializers.DateField(required=False, default=timezone.localdate)
    hospital_id = serializers.UUIDField(required=False, allow_null=True)
    prev_day_admissions = serializers.FloatField(min_value=0, max_value=100000, required=False)
    weekly_avg_admissions = serializers.FloatField(min_value=0, max_value=100000, required=False)

    def validate(self, attrs):
        has_previous = "prev_day_admissions" in attrs
        has_average = "weekly_avg_admissions" in attrs
        if has_previous != has_average:
            raise serializers.ValidationError(
                "Provide both prev_day_admissions and weekly_avg_admissions using actual admission records."
            )
        return attrs
