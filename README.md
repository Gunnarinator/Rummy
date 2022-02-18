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
