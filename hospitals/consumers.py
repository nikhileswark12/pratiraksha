import json

from channels.generic.websocket import AsyncWebsocketConsumer


class HospitalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated or not self.user.is_active:
            await self.close()
            return

        if self.user.role == "operator" and self.user.tenant_id:
            self.group_name = f"hospital_updates_tenant_{self.user.tenant_id}"
        elif self.user.role == "hospital_manager" and self.user.hospital_id:
            self.group_name = f"hospital_updates_{self.user.hospital_id}"
        else:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        await self.close(code=1008)

    async def _send_event(self, event, event_type):
        payload = {key: value for key, value in event.items() if key != "type"}
        await self.send(text_data=json.dumps({"type": event_type, **payload}, default=str))

    async def hospital_updated(self, event):
        await self._send_event(event, "hospital.updated")

    async def hospital_critical(self, event):
        await self._send_event(event, "hospital.critical")

    async def prediction_complete(self, event):
        await self._send_event(event, "prediction.complete")

    async def crisis_alert(self, event):
        await self._send_event(event, "crisis.alert")

    async def notification_new(self, event):
        await self._send_event(event, "notification.new")
