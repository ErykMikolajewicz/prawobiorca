import asyncio

SECURITY_MIN_RESPONSE_TIME = 2.0


async def prevent_timing_attack(execution_start_time: float) -> None:
    elapsed_execution_time = asyncio.get_running_loop().time() - execution_start_time
    delay = max(0.0, SECURITY_MIN_RESPONSE_TIME - elapsed_execution_time)
    await asyncio.sleep(delay)
