import os
import django
import threading
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pratiraksha.settings')
django.setup()

from django.db import connection

def hold_connection():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            time.sleep(10)
    except Exception as e:
        print(f"Error holding connection: {type(e).__name__} - {e}")
    finally:
        connection.close()

threads = []
for i in range(35):
    t = threading.Thread(target=hold_connection)
    threads.append(t)
    t.start()
    time.sleep(0.1) # stagger slightly

for t in threads:
    t.join()
