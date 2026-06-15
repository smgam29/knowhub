# extractors/base.py
# Defines the interface that every extractor must implement

from abc import ABC, abstractmethod

class BaseExtractor(ABC):
    
    @abstractmethod
    def extract(self, file_path: str) -> dict:
        # Takes a markdown file path
        # Returns {"entities": [...], "relationships": [...]} or None on failure
        pass