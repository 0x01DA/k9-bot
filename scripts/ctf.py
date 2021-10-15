#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
import click
from aiohttp import ClientSession
import logging
import asyncio
from bs4 import BeautifulSoup


async def team_info(teamid: str) -> str:
  uri = "https://ctftime.org/team/{}/".format(teamid)
  async with ClientSession() as session:
    async with session.get(uri) as resp:
      data = await resp.text()

  soup = BeautifulSoup(data, 'html.parser')
  container = soup.find_all("div", {"class": "container"})[1]
  rating = container.find("div", {"id": "rating_2021"})
  country = rating.find_all("p")
  country_rank = country[1].b.a.get_text()
  logging.debug(country[1].b.a.get_text())
  upcoming_text = container.table.get_text().split("\n",2)

  return "\nUpcoming:\n{}\n🇦🇹: {}\n".format(upcoming_text[2], country_rank)


async def ctf(req_type: str, teamid: str) -> str:
  uri = "https://ctftime.org/api/v1/{}/".format(req_type)
  output = ""

  if req_type == "teams":
    uri = uri + teamid + "/"
  elif req_type == "events":
    uri = uri + "?limit=5"
  async with ClientSession() as session:
    async with session.get(uri) as resp:
      data = await resp.json()
      logging.debug(data)
  if req_type == "teams":
    rating = data['rating']["2021"]
    upcoming_events = await team_info(teamid)
    output = "{}\nRating Points: {}\tRating Place: {}\n".format(data["name"], rating["rating_points"], rating["rating_place"])
    output += upcoming_events
  elif req_type == "events":
    for event in data:
      output += event["title"] + "\n\n"

  return output


@click.command()
@click.argument('type', default="teams", type=click.Choice(['teams', 'events', 'results', 'top', 'help']))
@click.option('--verbose', '-v', is_flag=True, help="Print more output.")
def main(type, verbose):
  if type == 'help':
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    return
  
  if verbose:
    logging.basicConfig(level=logging.DEBUG)

  logging.debug("Debug Logging Activated: 👾")
  config = "{}/config.rc".format(os.path.abspath(os.path.dirname(sys.argv[0])))
  load_dotenv(dotenv_path=config)
  teamid = os.getenv("CTF_TEAMID", default="translate")
  loop = asyncio.get_event_loop_policy().get_event_loop()
  output = loop.run_until_complete(ctf(type, teamid))
  print(output)


if __name__ == "__main__":
  main()
