import pytest
from unittest.mock import AsyncMock, MagicMock
from ..http_api import load_csv_data


@pytest.mark.asyncio
async def test_load_csv_data_success():
    csv_text = '\n'.join([
        'pool,feeding,start_time,duration,period,quantity',
        '1,1,350,540,3600,10',
        '1,2,351,530,1800,20',
        '2,1,352,550,3600,5',
        '2,2,353,580,2400,15',
    ])

    mock_hass = MagicMock()
    mock_hass.services.async_call = AsyncMock()

    results = await load_csv_data(csv_text, mock_hass)

    assert mock_hass.services.async_call.call_count == 4 * 4

    assert results['results'][0]['start_time'] == 350
    assert results['results'][1]['duration'] == 530


@pytest.mark.asyncio
async def test_load_csv_data_failed():
    csv_text = '\n'.join([
        'pool,feeding,start_time,duration,period',
        '1,1,350,540,3600',
        '1,2,351,530,1800',
        '2,1,352,550,3600',
        '2,2,353,580,2400',
    ])

    mock_hass = MagicMock()
    mock_hass.services.async_call = AsyncMock()

    results = await load_csv_data(csv_text, mock_hass)

    assert results['errors']
    assert not results['results']


@pytest.mark.asyncio
async def test_load_csv_data_failed2():
    csv_text = '\n'.join([
        'pool,feeding,start_time,duration,period,quantity',
        '1,1,350,540,3600,10',
        '1,2,351,530,1800,a20',
        '2,1,352,550,3600,5',
        '2,2,353,580,2400,15',
    ])

    mock_hass = MagicMock()
    mock_hass.services.async_call = AsyncMock()

    results = await load_csv_data(csv_text, mock_hass)

    assert results['results'][1]['errors']
