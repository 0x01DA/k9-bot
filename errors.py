#!/usr/bin/env python3

r"""errors.py.

Don't change tabbing, spacing, or formating as the
file is automatically linted and beautified.

"""


class ConfigError(RuntimeError):
    """Error encountered during reading the config file.

    Arguments:
    ---------
        msg (str): The message displayed to the user on error

    """

    def __init__(self, msg):
        """Set up."""
        super(ConfigError, self).__init__("%s" % (msg,))
