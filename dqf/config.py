"""Configuration management."""
from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any, Optional

from .types import CredentialsType


class Config:

    def __init__(
        self,
        config_filename: Optional[str] = 'dqf.toml',
        config_dict: Optional[dict[str, Any]] = None,
    ) -> None:
        if config_filename != 'dqf.toml' and config_dict:
            raise ValueError(
                'Provide either config_filename or config_dict, not both'
            )

        self.config_file = config_filename if not config_dict else None
        self.config = {}

        if config_dict:
            self.config = config_dict
        else:
            self.load_config()

    @classmethod
    def from_file(cls, config_filename: str = 'dqf.toml') -> Config:
        return cls(config_filename=config_filename)

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> Config:
        return cls(config_dict=config_dict)

    def load_config(self):
        if not self.config_file:
            raise ValueError('No config file specified')

        config_path = Path(self.config_file)
        if not config_path.exists():
            raise FileNotFoundError(
                f'Configuration file not found: {self.config_file}'
            )

        with open(config_path, 'rb') as f:
            self.config = tomllib.load(f)

    def _get_dqf(self):
        return self.config.get('dqf', {})

    def get_log_level(self):
        return self._get_dqf().get('log_level', 'info')

    def get_log_file(self):
        return self._get_dqf().get('log_file', 'dqf.log')

    def get_log_db_url(self) -> str | None:
        log_db_url: str | None = self._get_dqf().get('log_db_url')
        return log_db_url

    def get_db_url(self, query_name=None):
        if query_name and 'queries' in self.config:
            query_config = self.config['queries'].get(query_name, {})
            if 'db_url' in query_config:
                return query_config['db_url']

        if 'queries' in self.config and 'db_url' in self.config['queries']:
            return self.config['queries']['db_url']

        db_url = os.environ.get('DB_FWD_DB_URL')
        if not db_url:
            raise ValueError('Database URL not configured')
        return db_url

    def get_query(self, query_name):
        if (
            'queries' not in self.config
            or query_name not in self.config['queries']
        ):
            raise ValueError(
                f"Query '{query_name}' not found in configuration"
            )

        query_config = self.config['queries'][query_name]
        if 'query' not in query_config:
            raise ValueError(f"No query defined for '{query_name}'")

        return query_config['query']

    def get_api_url(self, query_name):
        if 'queries' in self.config and query_name in self.config['queries']:
            query_config = self.config['queries'][query_name]
            if 'api_url' in query_config:
                return query_config['api_url']

        if 'queries' in self.config and 'api_url' in self.config['queries']:
            return self.config['queries']['api_url']

        raise ValueError(f"API URL not configured for query '{query_name}'")

    def get_api_method(self, query_name: Optional[str] = None) -> str:
        method = None

        if (
            query_name
            and 'queries' in self.config
            and query_name in self.config['queries']
        ):
            method = self.config['queries'][query_name].get('api_method')

        if method is None and 'queries' in self.config:
            method = self.config['queries'].get('api_method')

        if method is None:
            return 'POST'

        method_upper: str = method.upper()
        if method_upper not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            raise ValueError(
                f'Unsupported api_method {method!r}. '
                "Supported values are 'POST', 'PUT', 'PATCH', 'DELETE'."
            )
        return method_upper

    def get_api_credentials(
        self, query_name: Optional[str] = None
    ) -> CredentialsType | None:
        username = password = None

        if (
            query_name
            and 'queries' in self.config
            and query_name in self.config['queries']
        ):
            query_config = self.config['queries'][query_name]
            username = query_config.get('api_username')
            password = query_config.get('api_password')

        if not username and 'queries' in self.config:
            username = self.config['queries'].get('api_username')
            password = self.config['queries'].get('api_password')

        if not username:
            username = os.environ.get('DB_FWD_API_USERNAME')
        if not password:
            password = os.environ.get('DB_FWD_API_PASSWORD')

        return (username, password) if username and password else None
