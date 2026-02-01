from typing import Iterable
from app.models import DisputeRequest, OtaQuote
from app.matching import match_dispute
from app.ota.gha import GoogleHotelAdsProvider
from app.ota.mmt import MakeMyTripProvider
from app.ota.agoda import AgodaProvider
from app.ota.booking import BookingProvider
from app.ota.skyscanner import SkyscannerProvider
from app.ota.mock import MockProvider
from app.config import settings


def provider_chain(ota: str) -> Iterable[object]:
    if settings.use_mock_ota:
        return [MockProvider()]

    providers = [GoogleHotelAdsProvider()]

    if ota == "mmt":
        providers.append(MakeMyTripProvider())
    elif ota == "agoda":
        providers.append(AgodaProvider())
    elif ota == "booking":
        providers.append(BookingProvider())
    elif ota == "skyscanner":
        providers.append(SkyscannerProvider())
    elif ota == "gha":
        pass
    else:
        raise ValueError("Unsupported OTA")

    return providers


def verify_dispute(req: DisputeRequest):
    quotes: list[OtaQuote] = []
    errors: list[str] = []

    for provider in provider_chain(req.ota):
        try:
            quote = provider.get_quote(req)
            quotes.append(quote)
        except NotImplementedError as exc:
            errors.append(str(exc))
        except RuntimeError as exc:
            msg = str(exc)
            if msg.startswith("ambiguous_rooms:"):
                errors.append(msg)
            else:
                errors.append(f"provider_error:{msg}")
        except Exception as exc:
            errors.append(f"provider_error:{exc}")

    best_quote = quotes[0] if quotes else None
    match = match_dispute(req, best_quote) if best_quote else None

    return best_quote, quotes, match, errors
