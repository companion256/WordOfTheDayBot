# Word of The Day

This script monitors the word of the day it will write a note to Nostr using the defined relays

- [Clone the repository](#clone-the-repository)
- [Preparation of Python Environment](#preparation-of-python-environment)
- [Configuring the Bot](#configuring-the-bot)
  - [Nostr Config](#nostr-config)
- [Running the Script](#running-the-script)
- [Running as a Service](#running-as-a-service)
- [For More Help](#for-more-help)

## Clone the repository

To setup bot, you'll first need to clone the repository

```sh
git clone https://github.com/companion256/WordOfTheDayBot.git
```

Change to the folder where the code is cloned to

```sh
cd WordOfTheDayBot
```

If you need to update the bot's code, pull the latest changes

```sh
git pull
```

## Preparation of Python Environment

To use this script, you'll need to run it with python 3.9 or higher and with the nostr, requests and bech32 packages installed.

First, create a virtual environment (or activate a common one)

```sh
python3 -m venv ~/.pyenv/wordofthedaybot
```

Activate it

```sh
source ~/.pyenv/wordofthedaybot/bin/activate
```

Install Dependencies

```sh
python3 -m pip install -r requirements.txt
```

## Configuring the Bot

A subdirectory for storing `data` will be created if one does not exist on first run of the script. Otherwise you can create and copy the sample configuration as follows:

```sh
mkdir -p data

cp -n sample-config.json data/config.json
```

Within this directory, a configuration file named `config.json` is read. If this file does not exist, one will be created using the `sample-config.json`.

The server configuration file is divided into a few key sections.

### Nostr Config

Edit the configuration

```sh
nano data/config.json
```

The `nostr` configuration section has these keys

| key     | description                               |
| ------- | ----------------------------------------- |
| nsec    | The nsec for identity                     |
| profile | The metadata fields for the bot's profile |
| relays  | The list of relays the bot uses           |

The most critical to define here is the `nsec`. You should generate an nsec on your own, and not use an existing one such as that for your personal usage.

The `profile` section contains fields that map to a nostr profile. The picture and banner should be URLs pointing to an image publicly available. The lud16 field is the lightning address that should be associated with the bot. A nip05 can optionally be set for external DNS verification as a nostr address.

The `relays` section contains the list of relays that the bot will use to read events and direct messages, as well as publish profiles (kind 0 metadata), direct message responses (kind 4), replies (kind 1). Each relay is configured with a url, and permissions for whether it can be read from or written to.

## Running the Script

Once configured, run the bot using the previously established virtual environment

```sh
~/.pyenv/WordOfTheDayBot/bin/python main.py
```

Press `Control+C` to stop the bot process when satisfied its running properly.

## Running as a Service

You can install a service to run the bot in the background. You will need to do this as sudo, and know the name of the user for which the code was installed under.

Copy the service file

```sh
sudo cp nostr-word-of-the-day-bot.service /etc/systemd/system/nostr-word-of-the-day-bot.service
```

Edit the contents

```sh
sudo nano -l /etc/systemd/system/nostr-word-of-the-day-bot.service
```

On lines 10, 11, and 12 change the username if you installed to a different user than `admin`.

Save (CTRL+O) and Exit (CTRL+X).

Enable and start the service

```sh
sudo systemctl enable nostr-word-of-the-day-bot.service

sudo systemctl start nostr-word-of-the-day-bot.service
```

## For More Help

For further assistance or customizations, reach out to the developer on Nostr

- NIP05: jay@thebitcoincompanion.com
- NPUB: npub1l8zv3fhdntxq00u3nmrxvmrwpenpgway8y67z663t92x6hd98w3qkfkw83
