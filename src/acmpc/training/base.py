"""Base trainer interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import torch


class BaseTrainer(ABC):
    """Abstract base class for all trainers."""

    @abstractmethod
    def train_step(self) -> dict[str, float]:
        """Execute one training step.

        Returns:
            Dictionary of training metrics.
        """
        pass

    @abstractmethod
    def evaluate(self) -> dict[str, float]:
        """Run evaluation episode(s).

        Returns:
            Dictionary of evaluation metrics.
        """
        pass

    @abstractmethod
    def save_checkpoint(self, path: Path) -> None:
        """Save trainer state to checkpoint file.

        Args:
            path: Path to save checkpoint.
        """
        pass

    @abstractmethod
    def load_checkpoint(self, path: Path) -> None:
        """Load trainer state from checkpoint file.

        Args:
            path: Path to checkpoint file.
        """
        pass

    @property
    @abstractmethod
    def device(self) -> torch.device:
        """Get the compute device."""
        pass

    @property
    @abstractmethod
    def global_step(self) -> int:
        """Get the current global training step."""
        pass

    @property
    @abstractmethod
    def epoch(self) -> int:
        """Get the current epoch."""
        pass

    @classmethod
    @abstractmethod
    def from_case(cls, case_config: Any, **kwargs) -> "BaseTrainer":
        """Create trainer from case configuration.

        Args:
            case_config: Case configuration object.
            **kwargs: Additional arguments.

        Returns:
            Initialized trainer instance.
        """
        pass
