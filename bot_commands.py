#!/usr/bin/env python3

r"""bot_commands.py.

See the implemented sample bot commands of `echo`, `date`, `dir`, `help`,
and `whoami`? Have a close look at them and style your commands after these
example commands.

Don't change tabbing, spacing, or formating as the
file is automatically linted and beautified.

"""

import getpass
import logging
import os
import glob
import json
import re  # regular expression matching
import subprocess
import yaml
from sys import platform
import traceback
from chat_functions import send_text_to_room

logger = logging.getLogger(__name__)

SERVER_ERROR_MSG = "Bot encountered an error. Here is the stack trace: \n"


class Command(object):
    """Use this class for your bot commands."""

    def __init__(self, client, store, config, command, room, event):
        """Set up bot commands.

        Arguments:
        ---------
            client (nio.AsyncClient): The client to communicate with Matrix
            store (Storage): Bot storage
            config (Config): Bot configuration parameters
            command (str): The command and arguments
            room (nio.rooms.MatrixRoom): The room the command was sent in
            event (nio.events.room_events.RoomMessageText): The event
                describing the command

        """
        self.client = client
        self.store = store
        self.config = config
        self.command = command
        self.room = room
        self.event = event
        # self.args: list : list of arguments
        self.args = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', self.command)[1:]
        self.aliases = self.getaliases()
        self.commandlower = self.command.lower()

    def getaliases(self):
        with open("aliases.yaml", 'r') as aliasfile:
            aliases = yaml.safe_load(aliasfile)
        for path in glob.glob("scripts/*"):
            if os.access(path, os.X_OK):
                script = os.path.split(path)[1]
                script_name, _ = os.path.splitext(script)
                if script in aliases:
                    aliases[script].append(script_name)
                else:
                    aliases[script] = [ script_name ]
        return aliases

    
    async def process(self):  # noqa
        """Process the command."""

        logger.debug(
            f"bot_commands :: Command.process: {self.command} {self.room}"
        )
        # echo
        if re.match("^echo$|^echo .*", self.commandlower):
            await self._echo()
        # help
        elif re.match(
            "^help$|^ayuda$|^man$|^manual$|^hilfe$|"
            "^help .*|^help.sh$",
            self.commandlower,
        ):
            await self._show_help()
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
        if not self.args:
            response = ("Ahoi, I'm K9!\nUse `commands` to view available commands.")
            await send_text_to_room(self.client, self.room.room_id, response)
            return

        topic = self.args[0]
        if topic == "rules":
            response = "These are the rules: Act responsibly."
        elif topic == "commands":
            aliases = json.dumps(self.aliases)
            response = (aliases)
            await send_text_to_room(self.client, self.room.room_id, response)
            return
        else:
            response = f"Unknown help topic `{topic}`!"
        await send_text_to_room(self.client, self.room.room_id, response)

    async def _unknown_command(self):
        await send_text_to_room(
            self.client,
            self.room.room_id,
            (
                f"Unknown command `{self.command}`. "
                "Try the `help` command for more information."
            ),
        )

    async def _os_cmd(
        self,
        cmd: str,
        args: list,
        markdown_convert=True,
        formatted=True,
        code=False,
        split=None,
    ):
        """Pass generic command on to the operating system.

        cmd (str): string of the command including any path,
            make sure command is found
            by operating system in its PATH for executables
            e.g. "date" for OS date command.
            cmd does not include any arguments.
            Valid example of cmd: "date"
            Invalid example for cmd: "echo 'Date'; date --utc"
            Invalid example for cmd: "echo 'Date' && date --utc"
            Invalid example for cmd: "TZ='America/Los_Angeles' date"
            If you have commands that consist of more than 1 command,
            put them into a shell or .bat script and call that script
            with any necessary arguments.
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
            run = subprocess.Popen(
                argv_list,  # list of argv
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
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


# EOF
