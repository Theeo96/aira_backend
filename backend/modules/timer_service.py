import asyncio
from typing import Awaitable, Callable


class TimerService:
    def __init__(
        self,
        on_fire: Callable[[int], Awaitable[None]],
        log=print,
    ):
        self.on_fire = on_fire
        self.log = log
        self._tasks: list[asyncio.Task] = []

    async def _run_timer(self, delay_sec: int):
        try:
            self.log(f"[Timer] scheduled: {delay_sec}s")
            await asyncio.sleep(delay_sec)
            self.log(f"[Timer] fired: {delay_sec}s")
            await self.on_fire(delay_sec)
        except asyncio.CancelledError:
            return
        except Exception as e:
            self.log(f"[Timer] schedule failed: {e}")

    async def register(self, timer_sec: int):
        task = asyncio.create_task(self._run_timer(timer_sec))
        self._tasks.append(task)

    def has_active(self):
        return any((not t.done()) for t in self._tasks)

    def cancel_all(self):
        canceled = 0
        for t in self._tasks:
            if not t.done():
                t.cancel()
                canceled += 1
        return canceled

    async def shutdown(self):
        for t in self._tasks:
            if not t.done():
                t.cancel()
        pending = [t for t in self._tasks if not t.done()]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

