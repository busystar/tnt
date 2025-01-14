# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.


import logging
from dataclasses import dataclass, field
from enum import auto, Enum
from typing import Any, Iterable, Optional

from torchtnt.runner.progress import Progress
from torchtnt.utils.timer import Timer

_logger: logging.Logger = logging.getLogger(__name__)


def _check_loop_condition(name: str, val: Optional[int]) -> None:
    if val is not None and val < 0:
        raise ValueError(
            f"Invalid value provided for {name}. Expected a non-negative integer or None, but received {val}."
        )


class EntryPoint(Enum):
    FIT = auto()
    TRAIN = auto()
    EVALUATE = auto()
    PREDICT = auto()


@dataclass
class PhaseState:
    """State for each phase (train, eval, predict)"""

    # pyre-ignore: Invalid type variable [34]
    dataloader: Iterable[Any]

    progress: Progress = field(default_factory=Progress)

    # Stopping conditions
    max_epochs: Optional[int] = None  # used only for train
    max_steps: Optional[int] = None  # used only for train
    max_steps_per_epoch: Optional[int] = None

    evaluate_every_n_steps: Optional[int] = None  # used only for evaluate
    evaluate_every_n_epochs: Optional[int] = None  # used only for evaluate

    # contains the output from the last call to the user's `*_step` method
    # pyre-ignore: Invalid type variable [34]
    step_output: Any = None

    def __post_init__(self) -> None:
        _check_loop_condition("max_epochs", self.max_epochs)
        _check_loop_condition("max_steps", self.max_steps)
        _check_loop_condition("max_steps_per_epoch", self.max_steps_per_epoch)
        _check_loop_condition("evaluate_every_n_steps", self.evaluate_every_n_steps)
        _check_loop_condition("evaluate_every_n_epochs", self.evaluate_every_n_epochs)


@dataclass
class State:
    """Parent State class which can contain up to 3 instances of PhaseState, for the 3 phases.

    A new State class is created (and the previous one erased) each time an entry point is called.
    """

    entry_point: EntryPoint
    timer: Timer = field(default_factory=Timer)

    train_state: Optional[PhaseState] = None
    eval_state: Optional[PhaseState] = None
    predict_state: Optional[PhaseState] = None

    _should_stop: bool = False

    def stop(self) -> None:
        """Signal to the loop to end after the current step completes."""
        _logger.warning("Received signal to stop")
        self._should_stop = True

    @property
    def should_stop(self) -> bool:
        """Read-only property for whether to terminate the loop after the current step completes."""
        return self._should_stop
