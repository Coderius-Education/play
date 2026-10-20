"""Start a task eagerly on Python 3.11, which has no asyncio.eager_task_factory."""

import asyncio
from asyncio import tasks as _tasks


class _HandStartedTask(_tasks._PyTask):  # pylint: disable=too-few-public-methods
    """A task whose first step is taken by hand, as eager_task_factory does on Python 3.12+."""

    _skip_the_scheduled_first_step = True

    def _Task__step(self, exc=None):  # pylint: disable=invalid-name
        """Skip the step that Task.__init__ scheduled, as take_first_step takes it."""
        if self._skip_the_scheduled_first_step:
            self._skip_the_scheduled_first_step = False
        else:
            super()._Task__step(exc)

    def _Task__wakeup(self, future):  # pylint: disable=invalid-name
        """Go on once *future* is done, passing on its error without raising it here first."""
        if future.cancelled():
            self._Task__step(future._make_cancelled_error())
        else:
            self._Task__step(future.exception())

    def take_first_step(self):
        """Take the first step now, with this task as its loop's current task."""
        outer = asyncio.current_task(self._loop)
        if outer is not None:
            _tasks._leave_task(self._loop, outer)
        try:
            self._context.run(super()._Task__step)
        finally:
            if outer is not None:
                _tasks._enter_task(self._loop, outer)


def eager_task_factory(loop, coro, *, name=None):
    """Run *coro* up to its first await as the task that then goes on with it."""
    task = _HandStartedTask(coro, loop=loop, name=name)
    task.take_first_step()
    return task
