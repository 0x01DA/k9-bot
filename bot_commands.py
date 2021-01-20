#!/usr/bin/env python3

import logging
import os
import glob
import json
import re
import subprocess
import yaml
import traceback
from chat_functions import send_text_to_room

logger = logging.getLogger(__name__)

SERVER_ERROR_MSG = "Bot encountered an error. Here is the stack trace: \n"


class Command(object):
    """Use this class for your bot commands."""

    def __init__(self, client, store, config, command, room, event):
        """Set up bot commands.
        """
        self.client = client
        self.store = store
        self.config = config
        self.command = command
        self.room = room
        self.event = event
        # self.args: list : list of arguments
        self.args = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', self.command)[1:]
        self.aliases = self.config.aliases
        self.scripts_dir = self.config.scripts_path_abs
        self.commandlower = self.command.lower().split()[0]


    
    async def process(self):  # noqa
        """Process the command."""

        logger.info(f"bot_commands :: Command.process: {self.command} {self.room.display_name} via {self.event}")
        # echo
        if re.match("^echo$|^echo .*", self.commandlower):
            await self._echo()
        # help
        elif re.match("^help$|^man$|^hilfe$|^help.sh$", self.commandlower):
            await self._show_help()
        elif re.match("^list$|^commands$|^ls$", self.commandlower):
            await self._list_commands()
        else:
            for command, alias in self.aliases.items():
              if self.commandlower in alias:
                await self._os_cmd(
                  cmd=command,
                  args=self.args,
                  markdown_convert=False,
                  formatted=True,
                  code=True,
                )

    async def _echo(self):
        """Echo back the command's arguments."""
        response = " ".join(self.args)
        if response.strip() == "":
            response = "echo!"
        await send_text_to_room(self.client, self.room.room_id, response)

    async def _show_help(self):
        """Show the help text."""
        response = ("Ahoi, I'm K9!\nUse `commands` to view available commands.")
        await send_text_to_room(self.client, self.room.room_id, response)
        return
    
    async def _list_commands(self):
        """List Commands.."""
        aliases = json.dumps(self.aliases, sort_keys=True, indent=4)
        response = (aliases)
        await send_text_to_room(self.client, self.room.room_id, response, code=True)
        return

    async def _unknown_command(self):
        await send_text_to_room(
            self.client,
            self.room.room_id,
            (f"Unknown command `{self.command}`. Try `commands` command for a list."),
        )

    async def _os_cmd(self,
        cmd: str,
        args: list,
        markdown_convert=True,
        formatted=True,
        code=False,
        split=None,
    ):
        """Pass generic command on to the operating system.

        cmd (str): string of the command including any path
        args (list): list of arguments
            Valid example: [ '--verbose', '--abc', '-d="hello world"']
        markdown_convert (bool): value for how to format response
        formatted (bool): value for how to format response
        code (bool): value for how to format response
        """
        try:
            # create a combined argv list, e.g. ['date', '--utc']
            argv_list = [cmd] + args
            logger.debug(
                f'OS command "{argv_list[0]}" with ' f'args: "{argv_list[1:]}"'
            )
            envirnoment = os.environ.copy()
            envirnoment["PATH"] = "{}:{}".format(self.scripts_dir, envirnoment["PATH"])
            envirnoment["K9_ROOM"] = self.room.display_name
            logger.debug(f'PATH: {envirnoment["PATH"]}')
            run = subprocess.Popen(
                argv_list,  # list of argv
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=envirnoment,
            )
            output, std_err = run.communicate()
            output = output.strip()
            std_err = std_err.strip()
            if run.returncode != 0:
                logger.debug(
                    f"Bot command {cmd} exited with return "
                    f"code {run.returncode} and "
                    f'stderr as "{std_err}" and '
                    f'stdout as "{output}"'
                )
                output = (
                    f"*** Error: command {cmd} returned error "
                    f"code {run.returncode}. ***\n{std_err}\n{output}"
                )
            response = output
        except Exception:
            response = SERVER_ERROR_MSG + traceback.format_exc()
            code = True  # format stack traces as code
        logger.debug(f"Sending this reply back: {response}")
        await send_text_to_room(
            self.client,
            self.room.room_id,
            response,
            markdown_convert=markdown_convert,
            formatted=formatted,
            code=code,
            split=split,
        )

