from rest_framework import serializers


class CrisisSimulationRequestSerializer(serializers.Serializer):
    scenario = serializers.ChoiceField(choices=("smog_alert", "heatwave", "mass_gathering"))
    hospital_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list, max_length=100
    )
    parameters = serializers.DictField(required=False, default=dict)

    def validate(self, attrs):
        scenario = attrs["scenario"]
        parameters = attrs["parameters"]
        schemas = {
            "smog_alert": {
                "aqi": serializers.FloatField(min_value=0, max_value=1000, required=False, default=100),
                "radius": serializers.FloatField(min_value=0.1, max_value=500, required=False, default=10),
            },
            "heatwave": {
                "temperature": serializers.FloatField(min_value=-50, max_value=70, required=False, default=35),
                "duration": serializers.IntegerField(min_value=1, max_value=14, required=False, default=1),
                "humidity": serializers.FloatField(min_value=0, max_value=100, required=False, default=50),
            },
            "mass_gathering": {
                "event_size": serializers.IntegerField(min_value=1, max_value=1000000, required=False, default=1000),
                "duration": serializers.IntegerField(min_value=1, max_value=168, required=False, default=5),
            },
        }
        parameter_serializer_class = type(
            "ScenarioParametersSerializer",
            (serializers.Serializer,),
            schemas[scenario],
        )
        parameter_serializer = parameter_serializer_class(data=parameters)
        if not parameter_serializer.is_valid():
            raise serializers.ValidationError({"parameters": parameter_serializer.errors})
        attrs["parameters"] = parameter_serializer.validated_data
        return attrs
