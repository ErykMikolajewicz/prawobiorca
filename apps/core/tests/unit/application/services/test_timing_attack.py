import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from core_service.application.services.security import SECURITY_MIN_RESPONSE_TIME, prevent_timing_attack


async def test_prevent_timing_attack_waits_for_remaining_time():
    elapsed_time = 0.5
    execution_start_time = asyncio.get_running_loop().time() - elapsed_time

    with patch("core_service.application.services.security.asyncio.sleep", new_callable=AsyncMock) as sleep:
        await prevent_timing_attack(execution_start_time)

    sleep.assert_awaited_once_with(pytest.approx(SECURITY_MIN_RESPONSE_TIME - elapsed_time, abs=0.1))


async def test_prevent_timing_attack_does_not_wait_after_min_response_time():
    execution_start_time = asyncio.get_running_loop().time() - SECURITY_MIN_RESPONSE_TIME - 1

    with patch("core_service.application.services.security.asyncio.sleep", new_callable=AsyncMock) as sleep:
        await prevent_timing_attack(execution_start_time)

    sleep.assert_awaited_once_with(0.0)
