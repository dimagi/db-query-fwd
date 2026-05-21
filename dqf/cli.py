"""Command-line interface."""

import argparse
import logging
import sys
from typing import Optional

from .config import Config
from .core import execute_query, forward_to_api
from .logging_handlers import DatabaseHandler


def set_up_logging(
    log_level_name: str,
    log_filename: str,
    log_db_url: Optional[str]
) -> None:
    if log_level_name.lower() == 'none':
        log_level = logging.CRITICAL + 1
    else:
        name_to_level = logging.getLevelNamesMapping()
        if log_level_name.upper() not in name_to_level:
            raise ValueError(f'Invalid log level {log_level_name!r}')
        log_level = name_to_level[log_level_name.upper()]

    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(file_handler)

    if log_db_url:
        db_handler = DatabaseHandler(log_db_url)
        logger.addHandler(db_handler)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Forwards a SQL query result to a web API endpoint.'
    )
    parser.add_argument(
        '--log-level',
        choices=['none', 'info', 'debug'],
        help='Logging level (overrides config file)',
    )
    parser.add_argument(
        '--log-file', help='Log file path (overrides config file)'
    )
    parser.add_argument(
        '--config-file',
        default='dqf.toml',
        help='Configuration file path (default: dqf.toml)',
    )
    parser.add_argument('query_name', help='Name of the query to execute')
    parser.add_argument(
        'query_params', nargs='*', help='Parameters for the query'
    )

    return parser.parse_args()


def main():
    args = parse_args()

    try:
        config = Config(args.config_file)

        log_level = args.log_level or config.get_log_level()
        log_file = args.log_file or config.get_log_file()
        log_db_url = config.get_log_db_url()
        set_up_logging(log_level, log_file, log_db_url)

        logging.info(f'Starting dqf for query: {args.query_name}')

        db_url = config.get_db_url(args.query_name)
        query = config.get_query(args.query_name)
        api_url = config.get_api_url(args.query_name)
        api_method = config.get_api_method(args.query_name)
        creds = config.get_api_credentials(args.query_name)

        result = execute_query(db_url, query, args.query_params)
        logging.debug(f'Query result: {result}')

        forward_to_api(api_url, result, creds, method=api_method)

        logging.info('Completed successfully')

    except Exception as e:
        logging.error(f'Error: {e}')
        sys.exit(1)
