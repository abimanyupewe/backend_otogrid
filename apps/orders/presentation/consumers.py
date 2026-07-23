"""
WebSockets Telemetry Consumer.
Handles real-time streaming of mechanic GPS coordinates during ON_THE_WAY order state.
"""
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class OrderConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket Consumer for order live telemetry stream.
    """

    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.room_group_name = f"order_{self.order_id}"

        # Join order channel group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"WebSocket Client terhubung ke group {self.room_group_name}")

    async def disconnect(self, close_code):
        # Leave order channel group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket Client terputus dari group {self.room_group_name}")

    async def receive_json(self, content, **kwargs):
        """
        Receives location payload from mechanic client.
        Expected payload:
        {
            "type": "location_update",
            "latitude": -6.175392,
            "longitude": 106.827153
        }
        """
        message_type = content.get("type")

        if message_type == "location_update":
            latitude = content.get("latitude")
            longitude = content.get("longitude")

            # Broadcast coordinates to all clients in group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "order_location_update",
                    "latitude": latitude,
                    "longitude": longitude,
                    "sender_channel_name": self.channel_name
                }
            )

    async def order_location_update(self, event):
        """
        Event handler receiving broadcast coordinates from group.
        Sends payload to connected WebSocket client.
        """
        await self.send_json({
            "type": "location_update",
            "latitude": event["latitude"],
            "longitude": event["longitude"]
        })
