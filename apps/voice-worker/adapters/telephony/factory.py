import logging
from typing import Optional
from core.interfaces import BaseTelephonyAdapter
from core.config import settings
from adapters.telephony.twilio_adapter import TwilioAdapter
from adapters.telephony.exotel_adapter import ExotelAdapter

logger = logging.getLogger("voice-worker.telephony.factory")


class TelephonyFactory:
    """Factory to instantiate the appropriate Telephony adapter based on configuration."""

    @staticmethod
    def get_adapter(provider: Optional[str] = None) -> BaseTelephonyAdapter:
        selected = (provider or settings.TELEPHONY_PROVIDER).lower()

        if selected == "twilio":
            logger.info("Instantiating TwilioAdapter...")
            return TwilioAdapter()
        elif selected == "exotel":
            logger.info("Instantiating ExotelAdapter...")
            return ExotelAdapter()
        else:
            logger.info(f"Telephony provider is '{selected}' (browser-only or none). Defaulting to mock Twilio.")
            return TwilioAdapter()
