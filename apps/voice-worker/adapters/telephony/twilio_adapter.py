import logging
from typing import Optional, Dict, Any
from core.interfaces import BaseTelephonyAdapter
from core.config import settings

logger = logging.getLogger("voice-worker.telephony.twilio")


class TwilioAdapter(BaseTelephonyAdapter):
    """
    Telephony Adapter using Twilio Voice & LiveKit SIP Outbound Dialing.
    Dials PSTN/GSM mobile numbers and directs audio into a LiveKit WebRTC room.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        sip_trunk_id: Optional[str] = None,
    ):
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.from_number = from_number or settings.TWILIO_PHONE_NUMBER
        self.sip_trunk_id = sip_trunk_id or settings.LIVEKIT_SIP_TRUNK_ID
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client successfully initialized.")
            except Exception as e:
                logger.warning(f"Failed to initialize Twilio client: {e}")

    async def dial_outbound(
        self, to_number: str, room_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Dispatches an outbound call through LiveKit SIP Trunk or Twilio REST.
        """
        logger.info(f"Initiating outbound Twilio call to {to_number} for room {room_name}")

        if not self._client or not self.from_number:
            logger.warning("Twilio credentials not configured. Returning simulated call result.")
            return {
                "status": "simulated",
                "to": to_number,
                "room_name": room_name,
                "provider": "twilio",
            }

        try:
            # When using LiveKit SIP trunk, you can invoke LiveKit SIP dispatch or Twilio Programmable Voice
            # Twilio TwiML routing to SIP URI: sip:<room_name>@<sip-domain>
            call = self._client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=f"https://handler.twilio.com/twiml/livekit-bridge?room={room_name}",
            )
            return {
                "status": "dialing",
                "call_sid": call.sid,
                "to": to_number,
                "room_name": room_name,
            }
        except Exception as e:
            logger.error(f"Failed to dial Twilio outbound call: {e}")
            raise e

    async def terminate_call(self, call_sid: str) -> bool:
        if not self._client:
            return True
        try:
            self._client.calls(call_sid).update(status="completed")
            return True
        except Exception as e:
            logger.error(f"Failed to terminate Twilio call {call_sid}: {e}")
            return False
