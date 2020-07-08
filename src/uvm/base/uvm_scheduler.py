
# import cocotb
from cocotb.triggers import Timer, Event
from .sv import sv


class UVMScheduler():
    """
    Simple zero-delay/nba scheduler for UVM to hide verilator event details.
    """

    inst = None

    @classmethod
    def get(cls):
        if UVMScheduler.inst is None:
            UVMScheduler.inst = UVMScheduler()
        return UVMScheduler.inst


    def __init__(self):
        self.zero_delay = []
        self.nba_region = []
        self.zero_delay_empty = Event('zero_delay_empty')
        self.enabled = False

    async def run_event_loop(self):
        """
        Each full iteration of the event loop advances simulation by one
        TIMEPRECISION unit.
        """
        self.enabled = True
        while self.enabled:
            while self.has_events() and self.enabled:
                while len(self.zero_delay) > 0:
                    evt, obj = self.zero_delay.pop(0)
                    evt.set()
                while len(self.nba_region) > 0:
                    evt, obj = self.nba_region.pop(0)
                    evt.set()
            await Timer(0)  # Advance simulation

    def has_events(self):
        return (len(self.zero_delay) > 0 or
            len(self.nba_region) > 0)


    async def wait_zero(self, obj):
        evt = Event('evt_0_' + str(sv.urandom()))
        self.zero_delay.append([evt, obj])
        await evt.wait()


    async def wait_nba(self, obj):
        evt = Event('evt_nba_' + str(sv.urandom()))
        self.nba_region.append([evt, obj])
        await evt.wait()


if UVMScheduler.inst is None:
    UVMScheduler.inst = UVMScheduler()
