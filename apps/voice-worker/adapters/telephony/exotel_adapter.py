import logging
import httpx
from typing import Optional, Dict, Any
from core.interfaces import BaseTelephonyAdapter
from core.config import settings

logger = logging.getLogger("voice-worker.telephony.exotel")


class ExotelAdapter(BaseTelephonyAdapter):
    """
    Telephony Adapter using Exotel Indian Telecom Routing.
    Used for cost-effective outbound calls in India to students over cellular networks.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_token: Optional[str] = None,
        subdomain: Optional[str] = None,
        caller_id: Optional[str] = None,
    ):
        self.api_key = api_key or settings.EXOTEL_API_KEY
        self.api_token = api_token or settings.EXOTEL_API_TOKEN
        self.subdomain = subdomain or settings.EXOTEL_SUBDOMAIN
        self.caller_id = caller_id or settings.EXOTEL_EXOPHONE
        self.base_url = (
            f"https://{self.api_key}:{self.api_token}@{self.subdomain}/v1/Accounts/{self.api_key}"
            if self.api_key and self.subdomain
            else None
        )

    async def dial_outbound(
        self, to_number: str, room_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Dials an Indian phone number via Exotel REST API.
        """
        logger.info(f"Initiating Exotel outbound call to {to_number} for room {room_name}")

        if not self.base_url or not self.caller_id:
            logger.warning("Exotel credentials incomplete. Returning simulated call result.")
            return {
                "status": "simulated",
                "to": to_number,
                "room_name": room_name,
                "provider": "exotel",
            }

        url = f"{self.base_url}/Calls/connect.json"
        data = {
            "From": to_number,
            "CallerId": self.caller_id,
            "Url": f"http://my.exotel.com/app/livekit_flow?room={room_name}",
            "CustomField": room_name,
        }

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(url, data=data, timeout=10.0)
                res.raise_for_status()
                result_json = res.json()
                logger.info(f"Exotel call initiated successfully: {result_json}")
                return {
                    "status": "dialing",
                    "provider": "exotel",
                    "call_details": result_json.get("Call", {}),
                }
        except Exception as e:
            logger.error(f"Exotel call trigger failed: {e}")
            raise e

    async def terminate_call(self, call_sid: str) -> bool:
        logger.info(f"Terminating Exotel call {call_sid}...")
        return True
