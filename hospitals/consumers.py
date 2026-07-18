import json
from channels.generic.websocket import AsyncWebsocketConsumer

class HospitalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Determine grouping based on role
        if self.user.role == 'operator':
            self.group_name = 'hospital_updates'
        elif self.user.role == 'hospital_manager':
            self.group_name = f'hospital_updates_{self.user.hospital_id}'
        else:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # We only push data, we don't expect client to send commands currently.
        pass

    # --- Event Handlers ---
    
    async def hospital_updated(self, event):
        """
        Handler for the 'hospital.updated' event type.
        """
        await self.send(text_data=json.dumps({
            'type': 'hospital.updated',
            'hospital_id': str(event.get('hospital_id')),
            'changes': event.get('changes', {}),
            'new_status': event.get('new_status')
        }))

    async def hospital_critical(self, event):
        """
        Handler for the 'hospital.critical' event type.
        """
        await self.send(text_data=json.dumps({
            'type': 'hospital.critical',
            'hospital_id': str(event.get('hospital_id')),
            'hospital_name': event.get('hospital_name'),
            'occupancy': event.get('occupancy')
        }))

    # --- Stubs for Future Days ---
    
    async def prediction_complete(self, event):
        # Stubbed for Day 18+
        pass

    async def crisis_alert(self, event):
        # Stubbed for Day 22+
        pass

    async def notification_new(self, event):
        # Stubbed for Day 25+
        pass
