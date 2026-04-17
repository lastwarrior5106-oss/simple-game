import pytest
from unittest.mock import AsyncMock, patch
from src.services.user_service import UserService
from src.models import User, Team
from src.errors import InsufficientCoinsError, TeamFullError, AlreadyInTeamError
from src.services.team_service import TeamService

async def test_level_up_unit():
    mock_user = User(id=1, level=1, coins=5000)
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_user)

    result = await UserService.level_up(1, mock_session)

    assert result.level == 2
    assert result.coins == 5025

async def test_create_user_unit():
    mock_session = AsyncMock()
    result = await UserService.create_user(mock_session)
    assert result.level == 1
    assert result.coins == 5000

