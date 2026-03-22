from typing import Any
from unittest.mock import AsyncMock

import pytest

from modules.auth.application.get_profile_use_case import GetProfileUseCase
from modules.auth.domain.exceptions import UserNotFoundException


async def test_get_profile_exists(
    mock_user_repo: AsyncMock,
    sample_user_data: dict[str, Any],
) -> None:
    use_case = GetProfileUseCase(mock_user_repo)
    result = await use_case.execute("test-uid-123")
    mock_user_repo.find_by_uid.assert_called_once_with("test-uid-123")
    assert result == sample_user_data


async def test_get_profile_not_found(
    mock_user_repo: AsyncMock,
) -> None:
    mock_user_repo.find_by_uid = AsyncMock(return_value=None)
    use_case = GetProfileUseCase(mock_user_repo)
    with pytest.raises(UserNotFoundException):
        await use_case.execute("unknown-uid")
