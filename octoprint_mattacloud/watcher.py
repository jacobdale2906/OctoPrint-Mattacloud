import os
import re
import time
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


class ImageHandler(PatternMatchingEventHandler):
    """
    Top level Mattacloud file watching class extending
    Watchdog's PatternMatchingEventHandler object.
    """
    pass