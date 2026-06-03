from abc import ABC, abstractmethod
from typing import List, Dict, Any

class AFLDataProvider(ABC):
    @abstractmethod
    def get_teams(self) -> List[Dict[str, Any]]:
        """Fetch all AFL teams."""
        pass

    @abstractmethod
    def get_matches(self, year: int) -> List[Dict[str, Any]]:
        """Fetch all matches for a given year."""
        pass
