import datetime

import pytest
from unittest.mock import AsyncMock, MagicMock
from ..http_api import load_csv_data


@pytest.mark.asyncio
async def test_load_csv_data_success():
    csv_text = '\n'.join([
        'pool,feeding,start_time,duration,period,quantity',
        '1,1,05:50:00,00:01:59,01:00:00,10',
        '1,2,05:51:00,00:00:50,01:01:01,20',
        '2,1,05:52:00,00:00:59,02:00:00,3600,5',
        '2,2,05:53:00,00:00:59,03:00:00,2400,15',
    ])

    mock_hass = MagicMock()
    mock_hass.services.async_call = AsyncMock()

    results = await load_csv_data(csv_text, mock_hass)

    assert mock_hass.services.async_call.call_count == 4 * 4

    assert results['results'][0]['start_time'] == 350
    assert results['results'][1]['duration'] == 50


@pytest.mark.asyncio
async def test_load_csv_data_failed():
    csv_text = '\n'.join([
        'pool,feeding,start_time,duration,period',
        '1,1,05:50:00,09:00:00,3600',
        '1,2,05:51:00,09:10:00,1800',
        '2,1,05:52:00,09:20:00,3600',
        '2,2,05:53:00,09:30:00,2400',
    ])

    mock_hass = MagicMock()
    mock_hass.services.async_call = AsyncMock()

    results = await load_csv_data(csv_text, mock_hass)

    assert results['error']


@pytest.mark.asyncio
async def test_load_csv_data_failed2():
    csv_text = '\n'.join([
        'pool,feeding,start_time,duration,period,quantity',
        '1,1,05:50:00,00:01:59,01:00:00,10',
        '1,2,05:51:00,00:00:50,01:01:01,a20',
        '2,1,05:52:00,00:00:59,02:00:00,3600,5',
        '2,2,05:53:00,09:00:59,03:00:00,2400,15',
    ])

    mock_hass = MagicMock()
    mock_hass.services.async_call = AsyncMock()

    results = await load_csv_data(csv_text, mock_hass)

    assert results['results'][1]['errors']
    assert results['results'][3]['errors']
