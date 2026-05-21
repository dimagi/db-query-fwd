# Spec: Configurable `api_method`

## Summary

Add an `api_method` configuration option so DQF can forward query
results using HTTP methods other than POST (e.g. PUT, PATCH). The
default behaviour remains unchanged (POST).


## Motivation

DHIS2 and other target APIs sometimes expect data to be sent with PUT or
PATCH semantics (e.g. updating an existing data value set). DQF
currently hard-codes `requests.post()` in `forward_to_api()`, which
prevents using DQF for those endpoints.


## Configuration

`api_method` follows the same precedence rules as `api_url`:

1. `queries.queryname.api_method` (per-query override)
2. `queries.api_method` (default for all queries)
3. Implicit default: `POST`

Valid values (case-insensitive): `POST`, `PUT`, `PATCH`, `DELETE`. The
value is normalised to uppercase before use. Any other value raises a
`ValueError` from the `Config` layer at lookup time, matching how
invalid log levels are reported.

`GET` and `HEAD` are not supported because DQF always sends a JSON
payload; allowing them would be misleading.

### Example `dqf.toml`

```toml
[queries]
db_url = '...'
api_username = '...'
api_password = '...'
api_method = 'PUT'   # default for all queries below

[queries.update_dataset]
query = "SELECT json_payload FROM ds_view WHERE period = :param1;"
api_url = 'https://dhis2.example.com/api/dataValueSets'
api_method = 'PUT'   # overrides the queries-level value

[queries.create_event]
query = "SELECT json_payload FROM events_view WHERE id = :param1;"
api_url = 'https://dhis2.example.com/api/events'
api_method = 'POST'
```


## Code changes

### `dqf/config.py`

Add a `get_api_method(query_name)` method mirroring `get_api_url()`:

- Look up `api_method` at the query level, then the `queries` level.
- If neither is set, return `'POST'`.
- Validate the value is in `{'POST', 'PUT', 'PATCH', 'DELETE'}`
  (case-insensitive). Raise `ValueError` with a clear message on
  invalid input.
- Return the uppercased string.

### `dqf/core.py`

Change `forward_to_api()` to accept a `method` parameter:

```python
def forward_to_api(
    api_url: str,
    payload: Any,
    credentials: Optional[CredentialsType] = None,
    method: str = 'POST',
) -> requests.Response:
    ...
    response = requests.request(
        method,
        api_url,
        json=payload,
        auth=credentials,
        headers={'Content-Type': 'application/json'},
    )
    ...
```

The existing log line for the request becomes:

```
logging.info(f'Forwarding to API: {method} {api_url}')
```

so the chosen method is visible in the log.

### `dqf/cli.py`

In `main()`, fetch the method and pass it through:

```python
api_method = config.get_api_method(args.query_name)
...
forward_to_api(api_url, result, creds, method=api_method)
```


## Tests

Add tests under `dqf/tests/` covering:

1. `Config.get_api_method` returns `'POST'` when nothing is configured.
2. `Config.get_api_method` returns the `queries`-level value when no
   per-query value is set.
3. `Config.get_api_method` returns the per-query value when both are
   set (override behaviour).
4. `Config.get_api_method` uppercases lowercase input (`'put'` →
   `'PUT'`).
5. `Config.get_api_method` raises `ValueError` for an unsupported value
   (e.g. `'GET'`, `'FROBNICATE'`).
6. `forward_to_api` issues a PUT request when `method='PUT'`, using
   `responses` or `requests-mock` (whichever the existing test suite
   uses) to assert the method on the captured request.
7. `forward_to_api` still defaults to POST when `method` is omitted
   (regression guard for existing behaviour).


## Documentation updates

### `README.md`

- In the "Configuration File" example, add an `api_method` line to
  illustrate usage.
- Under the `queries` section description, add:

  > `api_method` is the HTTP method used to forward query results.
  > Supported values are `POST` (default), `PUT`, `PATCH`, and
  > `DELETE`. A query can override this value by specifying
  > `api_method` in its section.

- Under the `queries.queryname` section description, add an
  `api_method` paragraph mirroring `api_url`'s override note.

### `dqf.toml.example`

Add commented examples at both the `queries` level and inside a
`queries.queryname` section, e.g.:

```toml
[queries]
# api_method = 'POST'  # Default. Supported: POST, PUT, PATCH, DELETE.

[queries.queryname1]
# api_method = 'PUT'   # Overrides the queries-level value.
```


## Out of scope

- Custom HTTP methods beyond the supported set.
- Per-request method selection from the command line.
- Changing the `Content-Type` header or supporting non-JSON bodies.
