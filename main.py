from logging.handlers import RotatingFileHandler
from nostr.event import Event, EventKind
import json
import logging
import requests
import shutil
import sys
import time
import libfiles as files
import libnostr as nostr
import libutils as utils

def validateConfig():
    if len(config.keys()) == 0:
        shutil.copy("sample-config.json", f"{files.dataFolder}config.json")
        logger.info(f"Copied sample-config.json to {files.dataFolder}config.json")
        logger.info("You will need to modify this file to setup nostr and bitcoin sections")
        quit()

def getBlockHeight():
    if "bitcoin" in config:
        if "url" in config["bitcoin"]:
            url = config["bitcoin"]["url"]
            try:
                response = requests.get(url=url)
                output = response.text
                if output.isnumeric():
                    return int(output)
            except Exception as e:
                logger.warning(f"Error fetching blockheight: {e}")
                return 0
    logger.warning(f"Could not get blockheight from API. Check config file for bitcoin.url")
    return 0

def makeProfileFromDict(profile, pubkey):
    j = {}
    kset = ("name","about","description","nip05","lud16","picture","banner")
    for k in kset: 
        if k in profile and len(profile[k]) > 0: j[k] = profile[k]
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

LOG_FILE = f"{files.logFolder}word_of_the_day_bot.log"
CONFIG_FILE = f"{files.dataFolder}config.json"
DATA_FILE = f"{files.dataFolder}saved_data.json"

if __name__ == '__main__':

    startTime, _ = utils.getTimes()

    # Logging to systemd
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
    stdoutLoggingHandler = logging.StreamHandler(stream=sys.stdout)
    stdoutLoggingHandler.setFormatter(formatter)
    logging.Formatter.converter = time.gmtime
    logger.addHandler(stdoutLoggingHandler)
    logFile = LOG_FILE
    fileLoggingHandler = RotatingFileHandler(logFile, mode='a', maxBytes=10*1024*1024, backupCount=21, encoding=None, delay=0)
    fileLoggingHandler.setFormatter(formatter)
    logger.addHandler(fileLoggingHandler)
    files.logger = logger
    nostr.logger = logger

    # Load server config
    config = files.getConfig(CONFIG_FILE)
    validateConfig()
    nostr.config = config["nostr"]

    matchon = {"value":"69","type":"contains","text":"NICE"}
    if "matchon" in config: matchon = config["matchon"]
    matchvalue = matchon["value"]
    matchtype = matchon["type"]
    matchtext = matchon["text"]

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
        blockheightCurrent = getBlockHeight()
        if blockheightCurrent > savedData[BLOCKHEIGHT_SEEN]:

            logger.debug(f"New Blockheight is {blockheightCurrent}") 

            # NEW BLOCK!
            changed = True
            isconnected = False

            # Process each block from already seen to the new block
            for blockHeight in range(savedData[BLOCKHEIGHT_SEEN] + 1, blockheightCurrent + 1):
                logger.debug(f"Checking {blockHeight} for {matchvalue}...")
                matched = False
                if matchtype == "contains":
                    if matchvalue in str(blockHeight): 
                        matched = True
                if matchtype == "startswith":
                    if str(blockHeight).startswith(matchvalue):
                        matched = True
                if matchtype == "endswith":
                    if str(blockHeight).endswith(matchvalue):
                        matched = True
                if matchtype == "modulus":
                    if str(matchvalue).isnumeric():
                        if blockHeight % int(matchvalue) == 0:
                            matched = True

                if matched:

                    logger.info(f"Block {blockHeight} {matchtype} {matchvalue} success!")

                    # Connect to relays if not yet connected
                    if not isconnected: 
                        nostr.connectToRelays()
                        isconnected = True

                    # Prepare, sign, and publish message to nostr for this block
                    event = Event(content=matchtext, kind=1, tags=[["blockheight",str(blockHeight)]])
                    nostr.getPrivateKey().sign_event(event)
                    nostr._relayManager.publish_event(event)
                    time.sleep(nostr._relayPublishTime)

                    # Make note of last reported
                    savedData[BLOCKHEIGHT_REPORTED] = blockHeight

            logger.debug("Done checks")

            # Disconnect if we connected
            if isconnected: nostr.disconnectRelays()

            # Update our last seen
            savedData[BLOCKHEIGHT_SEEN] = blockheightCurrent
            
            # Record state
            logger.debug("Saving state")
            files.saveJsonFile(DATA_FILE, savedData)

        # Rest a bit
        logger.debug("Sleeping for 1 minute")
        time.sleep(60)
