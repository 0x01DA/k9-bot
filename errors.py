#!/usr/bin/env python3

r"""
errors.py.
"""


class ConfigError(RuntimeError):
    """Error encountered during reading the config file.
    """

    def __init__(self, msg: str):
        """Set up."""
        super(ConfigError, self).__init__("%s" % (msg,))
