from logging.handlers import RotatingFileHandler
from nostr.event import Event
import logging
import shutil
import sys
import time
import files as files
import nostr as nostr
import utils as utils


def publishBotProfile():
    profile = nostr.config["profile"]
    profilePK = nostr.getPrivateKey()
    pubkey = profilePK.public_key.hex()
    kind0 = makeProfileFromDict(profile, pubkey)
    profilePK.sign_event(kind0)
    nostr.connectToRelays()
    nostr._relayManager.publish_event(kind0)
    time.sleep(nostr._relayPublishTime)
    nostr.disconnectRelays()


def makeProfileFromDict(profile, pubkey):
    j = {}
    kset = ("name", "about", "description", "nip05", "lud16", "picture", "banner")
    for k in kset:
        if k in profile and len(profile[k]) > 0:
            j[k] = profile[k]
    if "description" in j and "about" not in j:
        j["about"] = j["description"]
        del j["description"]
    content = json.dumps(j)
    kind0 = Event(
        content=content,
        public_key=pubkey,
        kind=EventKind.SET_METADATA,
    )
    return kind0


def validateConfig():
    if len(config.keys()) == 0:
        shutil.copy("sample-config.json", f"{files.dataFolder}-config.json")
        logger.info(f"Copied sample-config.json to {files.dataFolder}config.json")
        logger.info(
            "You will need to modify this file to setup nostr and bitcoin sections"
        )
        quit()


def getWordOfTheDay():
    logger.warning("Implement This.")
    pass


LOG_FILE = f"{files.logFolder}-word_of_the_day_bot.log"
CONFIG_FILE = f"{files.dataFolder}-config.json"
DATA_FILE = f"{files.dataFolder}-saved_data.json"

if __name__ == "__main__":
    startTime, _ = utils.getTimes()

    # Logging to systemd
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )
    stdoutLoggingHandler = logging.StreamHandler(stream=sys.stdout)
    stdoutLoggingHandler.setFormatter(formatter)
    logging.Formatter.converter = time.gmtime
    logger.addHandler(stdoutLoggingHandler)
    logFile = LOG_FILE
    fileLoggingHandler = RotatingFileHandler(
        logFile,
        mode="a",
        maxBytes=10 * 1024 * 1024,
        backupCount=21,
        encoding=None,
        delay=0,
    )
    fileLoggingHandler.setFormatter(formatter)
    logger.addHandler(fileLoggingHandler)
    files.logger = logger
    nostr.logger = logger

    # Load server config
    config = files.getConfig(CONFIG_FILE)
    validateConfig()
    nostr.config = config["nostr"]

    # Report bot info
    logger.debug(f"Bot npub: {nostr.getPubkey().bech32()}")

    publishBotProfile()

    # Load last checked block height
    savedData = files.loadJsonFile(DATA_FILE, {})

    # Initialize empty data
    logger.debug("Initializing...")
    changed = False
    if BLOCKHEIGHT_SEEN not in savedData:
        changed = True
        savedData[BLOCKHEIGHT_SEEN] = getBlockHeight()
    if BLOCKHEIGHT_REPORTED not in savedData:
        changed = True
        savedData[BLOCKHEIGHT_REPORTED] = 69
    if changed:
        logger.debug("Saving state")
        files.saveJsonFile(DATA_FILE, savedData)
        time.sleep(5)

    # Run Forever
    while True:
        # just track if we made any changes this round
        changed = False

        # Check if new block
        word_of_the_day = getWordOfTheDay()

        logger.debug(f"New Word is {word_of_the_day}")

        # NEW WORD!
        changed = True
        is_connected = False

        logger.info(f"Word of the day {word_of_the_day}")

        # Connect to relays if not yet connected
        if not is_connected:
            nostr.connectToRelays()
            is_connected = True

        # Prepare, sign, and publish message to nostr for this block
        event = Event(content=matchtext, kind=1, tags=[["word of the day"]])
        nostr.getPrivateKey().sign_event(event)
        nostr._relayManager.publish_event(event)
        time.sleep(nostr._relayPublishTime)

        # Make note of last reported
        savedData[BLOCKHEIGHT_REPORTED] = blockHeight

        logger.debug("Done checks")

        # Disconnect if we connected
        if is_connected:
            nostr.disconnectRelays()

        # Update our last seen
        savedData[BLOCKHEIGHT_SEEN] = word_of_the_day

        # Record state
        logger.debug("Saving state")
        files.saveJsonFile(DATA_FILE, savedData)

        # Rest a bit
        logger.debug("Sleeping for 1 minute")
        time.sleep(60)
