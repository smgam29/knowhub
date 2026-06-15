# reconcilers/base.py
# Defines the interface that every reconciler must implement

from abc import ABC, abstractmethod

class BaseReconciler(ABC):

    @abstractmethod
    def reconcile(self, relationships_by_model: dict) -> list:
        # Takes a dict of relationships keyed by model name
        # {"claude": [...], "mistral": [...]}
        # Returns a single deduplicated, semantically merged list
        pass