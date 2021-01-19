# K9-bot

`K9-bot` is a [Matrix](https://matrix.org) bot based on the Python 3 bot template [nio-template](https://github.com/8go/nio-template) which in turn is based on the Matrix Python SDK called [matrix-nio](https://github.com/poljar/matrix-nio). The bot, the template and the SDK are all written in Python 3.

- emoji verification and handling of `to_device` messages
- sending of images and files (audio, video, pdf, etc.)


## Installation and Setup

```
cp docker-compose.yml.example docker-compose.yml
docker-compose build
```

Other hints:
- Create an account for your bot in some client, e.g. in Element
- Use this account (username, password) in `config.yaml` and let the bot create a `brand-new` device
- If device is not new e2ee will not work.
- Verify the bot via emoji-verify
- If desired reconfigure `config.yaml` to replace password with access token for added security

## Develop

To add a new script just place it in `script`.
To enable the script for the Bot make it executeable `chmod +x`.

