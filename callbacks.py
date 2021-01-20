#!/usr/bin/env python3

r"""callbacks.py.

This file implements the callbacks for
- receiving a text message
- receiving an invite
- performing an emoji verification (bot must run in forground as keyboard
  input is required).

Don't change tabbing, spacing, or formating as the
file is automatically linted and beautified.

"""

from bot_commands import Command
from message_responses import Message
from nio import (
    JoinError,
    KeyVerificationStart,
    KeyVerificationCancel,
    KeyVerificationKey,
    KeyVerificationMac,
    ToDeviceError,
    LocalProtocolError,
)
import logging
import traceback

logger = logging.getLogger(__name__)


class Callbacks(object):
    """Collection of all callbacks."""

    def __init__(self, client, store, config):
        """Initialize.

        Arguments:
        ---------
            client (nio.AsyncClient): nio client used to interact with matrix
            store (Storage): Bot storage
            config (Config): Bot configuration parameters

        """
        self.client = client
        self.store = store
        self.config = config
        self.command_prefix = config.command_prefix

    async def message(self, room, event):
        """Handle an incoming message event.

        Arguments:
        ---------
            room (nio.rooms.MatrixRoom): The room the event came from
            event (nio.events.room_events.RoomMessageText): The event
                defining the message

        """
        # Extract the message text
        msg = event.body

        # Ignore messages from ourselves
        if event.sender == self.client.user:
            return

        logger.debug(
            f"Bot message received for room {room.display_name} | "
            f"{room.user_name(event.sender)}: {msg}"
        )

        # Process as message if in a public room without command prefix
        has_command_prefix = msg.startswith(self.command_prefix)

        # room.member_count > 2 ... we assume a public room
        # room.member_count <= 2 ... we assume a DM
        if not has_command_prefix and room.member_count > 2:
            # General message listener
            message = Message(self.client, self.store,
                              self.config, msg, room, event)
            await message.process()
            return

        # Otherwise if this is in a 1-1 with the bot or features a command
        # prefix, treat it as a command
        if has_command_prefix:
            # Remove the command prefix
            msg = msg[len(self.command_prefix):]

        command = Command(self.client, self.store,
                          self.config, msg, room, event)
        await command.process()

    async def invite(self, room, event):
        """Handle an incoming invite event.

        If an invite is received, then join the room specified in the invite.
        """
        logger.debug(f"Got invite to {room.room_id} from {event.sender}.")

        # Attempt to join 3 times before giving up
        for attempt in range(3):
            result = await self.client.join(room.room_id)
            if type(result) == JoinError:
                logger.error(
                    f"Error joining room {room.room_id} (attempt %d): %s",
                    attempt, result.message,
                )
            else:
                break
        else:
            logger.error("Unable to join room: %s", room.room_id)

        # Successfully joined room
        logger.info(f"Joined {room.room_id}")


    async def accept_all_verify(self, event):  # noqa
        """This will accept all Emoji verification requests.
        """
        try:
            client = self.client
            if isinstance(event, KeyVerificationStart):  # first step
                """ first step: receive KeyVerificationStart
                KeyVerificationStart(
                    source={'content':
                            {'method': 'm.sas.v1',
                             'from_device': 'DEVICEIDXY',
                             'key_agreement_protocols':
                                ['curve25519-hkdf-sha256', 'curve25519'],
                             'hashes': ['sha256'],
                             'message_authentication_codes':
                                ['hkdf-hmac-sha256', 'hmac-sha256'],
                             'short_authentication_string':
                                ['decimal', 'emoji'],
                             'transaction_id': 'SomeTxId'
                             },
                            'type': 'm.key.verification.start',
                            'sender': '@user2:example.org'
                            },
                    sender='@user2:example.org',
                    transaction_id='SomeTxId',
                    from_device='DEVICEIDXY',
                    method='m.sas.v1',
                    key_agreement_protocols=[
                        'curve25519-hkdf-sha256', 'curve25519'],
                    hashes=['sha256'],
                    message_authentication_codes=[
                        'hkdf-hmac-sha256', 'hmac-sha256'],
                    short_authentication_string=['decimal', 'emoji'])
                """

                if "emoji" not in event.short_authentication_string:
                    estr = ("Other device does not support emoji verification "
                            f"{event.short_authentication_string}. Aborting.")
                    print(estr)
                    logger.info(estr)
                    return
                resp = await client.accept_key_verification(
                    event.transaction_id)
                if isinstance(resp, ToDeviceError):
                    estr = f"accept_key_verification() failed with {resp}"
                    print(estr)
                    logger.info(estr)

                sas = client.key_verifications[event.transaction_id]

                todevice_msg = sas.share_key()
                resp = await client.to_device(todevice_msg)
                if isinstance(resp, ToDeviceError):
                    estr = f"to_device() failed with {resp}"
                    print(estr)
                    logger.info(estr)

            elif isinstance(event, KeyVerificationCancel):  # anytime
                """ at any time: receive KeyVerificationCancel
                KeyVerificationCancel(source={
                    'content': {'code': 'm.mismatched_sas',
                                'reason': 'Mismatched authentication string',
                                'transaction_id': 'SomeTxId'},
                    'type': 'm.key.verification.cancel',
                    'sender': '@user2:example.org'},
                    sender='@user2:example.org',
                    transaction_id='SomeTxId',
                    code='m.mismatched_sas',
                    reason='Mismatched short authentication string')
                """

                # There is no need to issue a
                # client.cancel_key_verification(tx_id, reject=False)
                # here. The SAS flow is already cancelled.
                # We only need to inform the user.
                estr = (f"Verification has been cancelled by {event.sender} "
                        f"for reason \"{event.reason}\".")
                logger.info(estr)

            elif isinstance(event, KeyVerificationKey):  # second step
                """ Second step is to receive KeyVerificationKey
                KeyVerificationKey(
                    source={'content': {
                            'key': 'SomeCryptoKey',
                            'transaction_id': 'SomeTxId'},
                        'type': 'm.key.verification.key',
                        'sender': '@user2:example.org'
                    },
                    sender='@user2:example.org',
                    transaction_id='SomeTxId',
                    key='SomeCryptoKey')
                """
                sas = client.key_verifications[event.transaction_id]

                print(f"{sas.get_emoji()}")
                # don't log the emojis

                resp = await client.confirm_short_auth_string(
                    event.transaction_id)
                if isinstance(resp, ToDeviceError):
                    estr = ("confirm_short_auth_string() "
                            f"failed with {resp}")
                    logger.info(estr)

            elif isinstance(event, KeyVerificationMac):  # third step
                """ Third step is to receive KeyVerificationMac
                KeyVerificationMac(
                    source={'content': {
                        'mac': {'ed25519:DEVICEIDXY': 'SomeKey1',
                                'ed25519:SomeKey2': 'SomeKey3'},
                        'keys': 'SomeCryptoKey4',
                        'transaction_id': 'SomeTxId'},
                        'type': 'm.key.verification.mac',
                        'sender': '@user2:example.org'},
                    sender='@user2:example.org',
                    transaction_id='SomeTxId',
                    mac={'ed25519:DEVICEIDXY': 'SomeKey1',
                         'ed25519:SomeKey2': 'SomeKey3'},
                    keys='SomeCryptoKey4')
                """
                sas = client.key_verifications[event.transaction_id]
                try:
                    todevice_msg = sas.get_mac()
                except LocalProtocolError as e:
                    # e.g. it might have been cancelled by ourselves
                    estr = (f"Cancelled or protocol error: Reason: {e}.\n"
                            f"Verification with {event.sender} not concluded. "
                            "Try again?")
                    logger.info(estr)
                else:
                    resp = await client.to_device(todevice_msg)
                    if isinstance(resp, ToDeviceError):
                        estr = f"to_device failed with {resp}"
                        logger.info(estr)
                    estr = (f"sas.we_started_it = {sas.we_started_it}\n"
                            f"sas.sas_accepted = {sas.sas_accepted}\n"
                            f"sas.canceled = {sas.canceled}\n"
                            f"sas.timed_out = {sas.timed_out}\n"
                            f"sas.verified = {sas.verified}\n"
                            f"sas.verified_devices = {sas.verified_devices}\n\n"
                            "Emoji verification was successful!")
                    logger.info(estr)
            else:
                estr = (f"Received unexpected event type {type(event)}. "
                        f"Event is {event}. Event will be ignored.")
                logger.info(estr)
        except BaseException:
            estr = traceback.format_exc()
            print(estr)
            logger.info(estr)

