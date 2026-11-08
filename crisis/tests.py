from rest_framework.test import APITestCase

from .serializers import CrisisSimulationRequestSerializer


class CrisisSimulationRequestSerializerTests(APITestCase):
    def test_rejects_unknown_scenario(self):
        serializer = CrisisSimulationRequestSerializer(data={"scenario": "unknown"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("scenario", serializer.errors)

    def test_rejects_negative_smog_radius(self):
        serializer = CrisisSimulationRequestSerializer(data={
            "scenario": "smog_alert",
            "parameters": {"aqi": 200, "radius": -10},
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("parameters", serializer.errors)

    def test_rejects_unbounded_mass_gathering_duration(self):
        serializer = CrisisSimulationRequestSerializer(data={
            "scenario": "mass_gathering",
            "parameters": {"event_size": 1000, "duration": 999999},
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("parameters", serializer.errors)

    def test_accepts_valid_heatwave_parameters(self):
        serializer = CrisisSimulationRequestSerializer(data={
            "scenario": "heatwave",
            "parameters": {"temperature": 42, "duration": 2, "humidity": 50},
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
