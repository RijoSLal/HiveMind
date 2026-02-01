from abc import ABC, abstractmethod
from app.models import DisputeRequest, OtaQuote

class OtaProvider(ABC):
    @abstractmethod
    def get_quote(self, req: DisputeRequest) -> OtaQuote:
        raise NotImplementedError
