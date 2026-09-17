"""Keep bearer links, search queries and client addresses out of access logs."""
import logging
import re


class RedactAccessLog(logging.Filter):
    def filter(self, record):
        if isinstance(record.args, tuple) and len(record.args) == 5:
            _, method, target, version, status = record.args
            target = str(target).split("?", 1)[0]
            target = re.sub(r"(/email/(?:accept|decline)/)[^/]+", r"\1[REDACTED]", target)
            record.args = ("[client]", method, target, version, status)
        return True
