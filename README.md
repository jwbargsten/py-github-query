# py-github-query

Download github data using the graphql API.

## Requirements

- make
- internet connection
- python3
- a
  [github personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
  (PAT)

## Setup

```console
make setup
```

This will crate a virtual env and install the requirements.

Make sure you set `GITHUB_PAT` is set as environment variable when running e.g.
`make run`. Be aware that this token is like a password, so protect it carefully.
`py-github-query` supports `.env` files (see
[python-dotenv](https://pypi.org/project/python-dotenv/) for more info). You can supply
your github PAT via `.env`. Have a look at `.env.example` to get an idea what to put in
there.

## Run

By default the organisation `xebia` is used.

```console
make run
```

This command will create `./members.ndjson` and `./prs.ndjson`. They are in the
[ndjson](http://ndjson.org/) format (also called `jsonl`).

You can query a different organisation using:

```console
ORG=godatadriven make run
```
