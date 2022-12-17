import os
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
import logging
import json
import sys
import argparse
from inspect import getsourcefile
from textwrap import dedent


log_dfmt = "%Y-%m-%d %H:%M:%S"
log_fmt = "[%(asctime)s] [%(levelname)s] %(name)s.%(funcName)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=log_fmt, datefmt=log_dfmt)
logging.getLogger("gql").setLevel(logging.WARNING)


NAME, _ = os.path.splitext(os.path.basename(getsourcefile(lambda: 0)))
logger = logging.getLogger(NAME)


def calc_page_range(page, page_size):
    return (page - 1) * page_size + 1, (page * page_size)


def paginate(client, query, *, page_info_path, query_params=None, page_size=80):
    if query_params is None:
        query_params = {}
    res = {}
    hasNextPage = True
    after = None
    page = 1
    while hasNextPage:
        res = client.execute(
            query, {**query_params, "after": after, "first": page_size}
        )
        hasNextPage = get_path(res, f"{page_info_path}.hasNextPage")
        after = get_path(res, f"{page_info_path}.endCursor")
        credits_remaining = get_path(res, "rateLimit.remaining")
        start, end = calc_page_range(page, page_size)
        logger.info(
            f"page {page} ({start} - {end}), gh API credits remaining: {credits_remaining}"
        )
        yield res
        page += 1


def parse(args, *, client, members_cb, prs_cb):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    members_cmd = subparsers.add_parser(
        "members", help="retrieve the members of an org"
    )
    members_cmd.add_argument("org", type=str, help="the organisation, e.g. xebia")
    members_cmd.set_defaults(func=members_cb)

    prs_cmd = subparsers.add_parser("prs", help="download the prs")
    prs_cmd.add_argument(
        "members",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="list members in ndjson format (the output of the members subcmd)",
    )
    prs_cmd.set_defaults(func=prs_cb)
    parsed_args = parser.parse_args(args)
    parsed_args.func(parsed_args, client)


def get_path(data, p, default=None):
    parts = p.split(".")
    for part in parts[:-1]:
        data = data.get(part, {})
    return data.get(parts[-1], default)


def get_members(args, client):
    logger.info(f"retrieving members of organization {args.org}")
    query = gql(
        dedent(
            """\
        query getUsers($login: String!, $after: String, $first: Int) {
          organization(login: $login) {
            name
            login
            membersWithRole(after: $after, first: $first) {
              nodes {
                id
                login
                email
                name
              }
              pageInfo {
                endCursor
                hasNextPage
              }
            }
          }
          rateLimit {
            cost
            remaining
            resetAt
          }
        }
        """
        )
    )

    for res in paginate(
        client,
        query,
        query_params={"login": args.org},
        page_info_path="organization.membersWithRole.pageInfo",
    ):
        for user in get_path(res, "organization.membersWithRole.nodes"):
            print(json.dumps(user))


def get_prs(args, client):
    logger.info("retrieving pull requests")
    query = gql(
        dedent(
            """\
        query getPrs($login: String!, $after: String, $first: Int) {
          user(login: $login) {
            pullRequests(states: [MERGED], first: $first, after: $after) {
              nodes {
                author {
                  login
                }
                title
                bodyText
                url
                closedAt
                createdAt
                repository {
                  url
                  name: nameWithOwner
                }
              }
              pageInfo {
                endCursor
                hasNextPage
              }
            }
          }
          rateLimit {
            cost
            remaining
            resetAt
          }
        }
        """
        )
    )

    for member_raw in args.members:
        member = json.loads(member_raw)
        login = member["login"]
        logger.info(f"processing {login}")

        for res in paginate(
            client,
            query,
            query_params={"login": login},
            page_info_path="user.pullRequests.pageInfo",
        ):
            prs = get_path(res, "user.pullRequests.nodes", [])
            for pr in prs:
                print(json.dumps(pr))


token = os.environ["GITHUB_PAT"]
if not token:
    logger.fatal("no token defined, expecting valid token set via env var GITHUB_PAT")
    exit(1)
transport = AIOHTTPTransport(
    url="https://api.github.com/graphql", headers={"Authorization": f"bearer {token}"}
)

gql_client = Client(transport=transport)

parse(sys.argv[1:], members_cb=get_members, prs_cb=get_prs, client=gql_client)
