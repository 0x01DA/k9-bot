#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
import click
from aiohttp import ClientSession
import logging
import asyncio


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def ctf(req_type: str, teamid: str) -> str:
  uri = "https://ctftime.org/api/v1/{}/".format(req_type)
  output = ""

  if req_type == "teams":
    uri = uri + teamid + "/"
  if req_type == "events":
    uri = uri + "?limit=5"
  async with ClientSession() as session:
    async with session.get(uri) as resp:
      data = await resp.json()
  if req_type == "teams":
    rating = data['rating'][0]["2021"]
    output = "Rating Points: {}\tRating Place: {}\n".format(rating["rating_points"], rating["rating_place"])
  elif req_type == "events":
    for event in data:
      output += event["title"] + "\n\n"

  return output

@click.command()
@click.argument('type', default="teams", type=click.Choice(['teams', 'events', 'results', 'top', 'help']))
def main(type):
  if type == 'help':
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    return
  config = "{}/config.rc".format(os.path.abspath(os.path.dirname(sys.argv[0])))
  load_dotenv(dotenv_path=config)
  teamid = os.getenv("CTF_TEAMID", default="translate")
  loop = asyncio.get_event_loop()
  output = loop.run_until_complete(ctf(type, teamid))
  print(output)


if __name__ == "__main__":
  main()
