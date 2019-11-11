import sys
import unittest

from ert_shared.models import BaseRunModel
from ert_shared.tracker.events import (DetailedEvent, EndEvent, GeneralEvent,
                                       TickEvent)
from ert_shared.tracker.qt import QTimerTracker

if sys.version_info >= (3, 3):
    from unittest.mock import Mock
else:
    from mock import Mock


class QTimerTrackerTest(unittest.TestCase):

    def test_qtimers_are_instantiated_and_setup(self):
        intervals = [1, 2, 3]
        tracker = QTimerTracker(
            None, Mock, intervals[0], intervals[1], intervals[2], Mock())

        self.assertEqual(3, len(tracker._qtimers),
                         "tracker did not create three timers")
        for idx, interval in enumerate(intervals):
            timer = tracker._qtimers[idx]
            timer.setInterval.assert_called_once_with(interval*1000)
            timer.timeout.connect.assert_called_once()

    def test_end_events_are_emitted(self):
        event_handler = Mock()
        brm = BaseRunModel(None, phase_count=0)  # a finished model
        tracker = QTimerTracker(brm, Mock, 1, 0, 0, event_handler)

        tracker._tick()

        for idx, ev_cls in enumerate([TickEvent, GeneralEvent, DetailedEvent,
                                      EndEvent]):
            _, args, _ = event_handler.mock_calls[idx]
            self.assertIsInstance(args[0], ev_cls,
                                  "called with unexpected event")

    def test_qtimers_are_stopped_for_finished_model(self):
        brm = BaseRunModel(None, phase_count=0)  # a finished model
        tracker = QTimerTracker(brm, Mock, 1, 0, 0, Mock())

        tracker._tick()

        for timer in tracker._qtimers:
            timer.stop.assert_called_once()