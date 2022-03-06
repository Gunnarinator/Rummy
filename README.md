# Rummy

## Workspace Setup

### `pipenv`

Dependencies for Python are managed using [pipenv](https://pipenv.pypa.io/en/latest/).

Install using homebrew (macOS):
```
brew install pipenv
```

Install it using `pip`:

```
pip install --user pipenv
```

Once `pipenv` is installed, set up the workspace with:

```
pipenv install
```

### Running the Server

To run the server, run the following command:

```
pipenv run flask run
```

You can specify a host and/or port (default 500) using respective options (this example will listen everywhere on port 80):

```
pipenv run flask run --host=0.0.0.0 --port 80
```

## Architecture

Super Rummy uses a client-server architecture. Events are sent from the server to the client to notify them of changes in the board state, while actions are sent the other way to inform the server of the user's intent.

For more details, head over to the [architecture document](architecture.md).
