from rest_framework.test import APITestCase

from .serializers import PredictionRequestSerializer


class PredictionRequestSerializerTests(APITestCase):
    def test_rejects_non_numeric_environmental_input(self):
        serializer = PredictionRequestSerializer(data={"pollution_level": "high"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("pollution_level", serializer.errors)

    def test_rejects_out_of_range_environmental_input(self):
        serializer = PredictionRequestSerializer(data={"humidity": 150})
        self.assertFalse(serializer.is_valid())
        self.assertIn("humidity", serializer.errors)

    def test_requires_both_real_admission_features(self):
        serializer = PredictionRequestSerializer(data={"prev_day_admissions": 12})
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_accepts_valid_inputs_without_fabricated_admissions(self):
        serializer = PredictionRequestSerializer(data={
            "pollution_level": 80,
            "temperature": 30,
            "humidity": 60,
            "rainfall": 2,
            "date": "2026-11-08",
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
