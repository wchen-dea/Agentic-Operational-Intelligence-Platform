import logging
import sys
from datetime import datetime

import config

_props = config.get_application_properties()
_log_props = config.get_property_map(_props, "logging")
_level = logging.getLevelName(_log_props.get("log.level", "INFO"))
logging.basicConfig(stream=sys.stdout, level=_level, format="%(message)s")


def log_message(message, log_level=logging.INFO):
    if config.is_local() and log_level >= _level:
        print(
            {
                "messageType": logging.getLevelName(log_level),
                "message": str(message),
                "timestamp": datetime.now().isoformat(),
            }
        )
    else:
        logging.log(log_level, message)
