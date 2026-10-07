from django.core.management.base import BaseCommand
from django.utils import timezone
from hospitals.models import Hospital
from accounts.models import User
from pratiraksha.utils import get_mongo_db
import random
import uuid

class Command(BaseCommand):
    help = 'Seeds the database with 50+ Phase 1 hospitals'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding Phase 1 data...')
        
        # Ensure we have at least one operator user
        operator, created = User.objects.get_or_create(
            email='operator@example.com',
            defaults={
                'name': 'System Operator',
                'role': 'operator',
                'is_active': True
            }
        )
        if created:
            operator.set_password('password123')
            operator.save()
            self.stdout.write('Created operator user')

        regions = ['North', 'South', 'East', 'West', 'Central']
        statuses = ['NORMAL', 'NORMAL', 'NORMAL', 'MODERATE', 'MODERATE', 'CRITICAL']

        Hospital.objects.all().delete()
        
        hospitals_to_create = []
        for i in range(1, 55):
            total_beds = random.randint(100, 1500)
            status = random.choice(statuses)
            
            # set occupancy based on status
            if status == 'CRITICAL':
                occupancy = int(total_beds * random.uniform(0.9, 1.0))
            elif status == 'MODERATE':
                occupancy = int(total_beds * random.uniform(0.7, 0.89))
            else:
                occupancy = int(total_beds * random.uniform(0.4, 0.69))

            hospitals_to_create.append(
                Hospital(
                    id=uuid.uuid4(),
                    name=f'Hospital {i}',
                    address=f'{random.randint(1, 9999)} {random.choice(["Main St", "Oak Ave", "Pine Rd"])}',
                    zip_code=f'{random.randint(10000, 99999)}',
                    contact_number=f'555-{random.randint(1000, 9999)}',
                    email=f'contact@hospital{i}.org',
                    status=status,
                    total_capacity=total_beds,
                    current_occupancy=occupancy
                )
            )

        Hospital.objects.bulk_create(hospitals_to_create)
        self.stdout.write(f'Created {len(hospitals_to_create)} hospitals.')
        
        # Seed MongoDB Predictions
        db = get_mongo_db()
        if db is not None:
            # Clear existing
            db.predictions.delete_many({})
            db.activity_logs.delete_many({})
            
            predictions = []
            for i in range(100):
                predictions.append({
                    'id': str(uuid.uuid4()),
                    'risk_level': random.choice(['LOW', 'MEDIUM', 'HIGH']),
                    'risk_score': random.randint(10, 95),
                    'predicted_surge': random.randint(5, 40),
                    'confidence': random.uniform(60.0, 90.0),
                    'created_at': timezone.now() - timezone.timedelta(days=random.randint(0, 30))
                })
            if predictions:
                db.predictions.insert_many(predictions)
                self.stdout.write(f'Seeded {len(predictions)} predictions to MongoDB.')
        else:
            self.stdout.write(self.style.WARNING('MongoDB unavailable, skipped prediction seeding.'))

        self.stdout.write(self.style.SUCCESS('Seeding complete!'))

