"""Tests for API operations."""

import logging
import pytest
from unittest.mock import Mock, patch
import requests
from unmagic import get_request

from dqf import forward_to_api


@patch('dqf.core.requests.request')
def test_forward_to_api_success(mock_request):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"success": true}'
    mock_request.return_value = mock_response

    payload = {'test': 'data'}
    forward_to_api('https://example.com/api', payload, ('user', 'pass'))

    mock_request.assert_called_once_with(
        'POST',
        'https://example.com/api',
        json=payload,
        auth=('user', 'pass'),
        headers={'Content-Type': 'application/json'},
    )
    mock_response.raise_for_status.assert_called_once()


@patch('dqf.core.requests.request')
def test_forward_to_api_no_auth(mock_request):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"success": true}'
    mock_request.return_value = mock_response

    payload = {'test': 'data'}
    forward_to_api('https://example.com/api', payload, None)

    mock_request.assert_called_once_with(
        'POST',
        'https://example.com/api',
        json=payload,
        auth=None,
        headers={'Content-Type': 'application/json'},
    )


@patch('dqf.core.requests.request')
def test_forward_to_api_http_error(mock_request):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = 'Internal Server Error'
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        '500 Server Error'
    )
    mock_request.return_value = mock_response

    payload = {'test': 'data'}

    with pytest.raises(requests.exceptions.HTTPError):
        forward_to_api('https://example.com/api', payload, ('user', 'pass'))


@patch('dqf.core.requests.request')
def test_forward_to_api_connection_error(mock_request):
    mock_request.side_effect = requests.exceptions.ConnectionError(
        'Connection refused'
    )

    payload = {'test': 'data'}

    with pytest.raises(requests.exceptions.ConnectionError):
        forward_to_api('https://example.com/api', payload, ('user', 'pass'))


@patch('dqf.core.requests.request')
def test_forward_to_api_timeout(mock_request):
    mock_request.side_effect = requests.exceptions.Timeout('Request timed out')

    payload = {'test': 'data'}

    with pytest.raises(requests.exceptions.Timeout):
        forward_to_api('https://example.com/api', payload, ('user', 'pass'))


@patch('dqf.core.requests.request')
def test_forward_to_api_json_payload(mock_request):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"success": true}'
    mock_request.return_value = mock_response

    payload = '{"period": "2024Q1", "data": [1, 2, 3]}'

    forward_to_api('https://example.com/api', payload, ('user', 'pass'))

    call_kwargs = mock_request.call_args[1]
    assert call_kwargs['json'] == payload


@patch('dqf.core.requests.request')
def test_forward_to_api_logging(mock_request):
    log_capture = get_request().getfixturevalue('caplog')
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.text = '{"id": 123}'
    mock_request.return_value = mock_response

    payload = {'test': 'data'}

    with log_capture.at_level(logging.DEBUG):
        forward_to_api('https://example.com/api', payload, ('user', 'pass'))

    debug_records = [r for r in log_capture.records if r.levelname == 'DEBUG']
    assert len(debug_records) >= 2  # Request and response should be logged


@patch('dqf.core.requests.request')
def test_forward_to_api_put_method(mock_request):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"success": true}'
    mock_request.return_value = mock_response

    payload = {'test': 'data'}
    forward_to_api(
        'https://example.com/api', payload, ('user', 'pass'), method='PUT'
    )

    mock_request.assert_called_once_with(
        'PUT',
        'https://example.com/api',
        json=payload,
        auth=('user', 'pass'),
        headers={'Content-Type': 'application/json'},
    )


@patch('dqf.core.requests.request')
def test_forward_to_api_default_method_is_post(mock_request):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = ''
    mock_request.return_value = mock_response

    forward_to_api('https://example.com/api', {'x': 1})

    assert mock_request.call_args[0][0] == 'POST'
