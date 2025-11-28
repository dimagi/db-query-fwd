"""Core functionality."""

import logging
from typing import Any, Optional

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

type UsernameType = str
type PasswordType = str
type CredentialsType = tuple[UsernameType, PasswordType]


def execute_query(
    db_url: str,
    query: str,
    params: Optional[list[str]] = None,
    engine: Optional[Engine] = None,
) -> Any:
    if engine is None:
        engine = create_engine(db_url)

    if params:
        param_dict = {f'param{i+1}': param for i, param in enumerate(params)}
    else:
        param_dict = {}

    logging.info(f'Executing query: {query}')
    logging.debug(f'Query parameters: {param_dict}')

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), param_dict)
            rows = result.fetchmany(2)

            if not rows:
                raise ValueError('Query returned no results')

            if len(rows) > 1:
                raise ValueError('Query returned more than one row')

            row = rows[0]

            if len(row) != 1:
                raise ValueError('Query must return exactly one field')

            return row[0]
    except SQLAlchemyError as e:
        logging.error(f'Database error: {e}')
        raise


def forward_to_api(
    api_url: str,
    payload: Any,
    credentials: Optional[CredentialsType] = None,
) -> requests.Response:
    logging.info(f'Forwarding to API: {api_url}')
    logging.debug(f'API Request - URL: {api_url}, Payload: {payload}')

    response = requests.post(
        api_url,
        json=payload,
        auth=credentials,
        headers={'Content-Type': 'application/json'},
    )
    logging.info(f'API Response - Status: {response.status_code}')
    logging.debug(
        f'API Response - Status: {response.status_code}, '
        f'Body: {response.text}'
    )
    response.raise_for_status()

    return response
