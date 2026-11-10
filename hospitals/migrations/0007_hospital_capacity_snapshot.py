import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("hospitals", "0006_default_tenant")]

    operations = [
        migrations.CreateModel(
            name="HospitalCapacitySnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("current_occupancy", models.PositiveIntegerField()),
                ("total_capacity", models.PositiveIntegerField()),
                ("status", models.CharField(choices=[("NORMAL", "Normal"), ("MODERATE", "Moderate"), ("CRITICAL", "Critical")], max_length=50)),
                ("captured_at", models.DateTimeField(auto_now_add=True)),
                ("hospital", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="capacity_snapshots", to="hospitals.hospital")),
            ],
            options={"ordering": ["captured_at"]},
        ),
    ]
