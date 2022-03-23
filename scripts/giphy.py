#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
import click
from aiohttp import ClientSession
import logging
import asyncio
import aiofiles


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def giphy(search_term: str, endpoint: str, api_key: str, cache_dir: str, image_mode: bool) -> str:
  params = {"s": search_term, "api_key": api_key}
  uri = "http://api.giphy.com/v1/gifs/{}".format(endpoint)

  async with ClientSession() as session:
    async with session.get(uri, params=params) as resp:
      data = await resp.json()
    image_url = data['data']['images']['original']['url']
    if not image_mode:
      return image_url[:image_url.find('?')]
    image_path = "{}/{}.gif".format(cache_dir, data['data']['id'])
    if os.path.exists(image_path):
      return image_path
    async with session.get(image_url, params=params) as img_data:
      f = await aiofiles.open(image_path, mode='wb')
      await f.write(await img_data.read())
      await f.close()

  # return gif_link
  return image_path


@click.command()
@click.argument('search')
@click.option('--image', is_flag=True, default=True)
def main(search, image):
  image = False if os.path.basename(sys.argv[0]).startswith('giphy') else image
  config = "{}/config.rc".format(os.path.abspath(os.path.dirname(sys.argv[0])))
  load_dotenv(dotenv_path=config)
  logger.info(image)
  endpoint = os.getenv("GIPHY_ENDPOINT", default="translate")
  cache_dir = os.getenv("GIPHY_CACHE", default="/tmp/giphycache")
  api_key = os.getenv("GIPHY_API_KEY", default="")
  if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
  loop = asyncio.get_event_loop()
  output = loop.run_until_complete(giphy(search, endpoint, api_key, cache_dir, image))
  print(output)


if __name__ == "__main__":
  main()
