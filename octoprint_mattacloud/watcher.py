import re

from watchdog.events import PatternMatchingEventHandler


class ImageHandler(PatternMatchingEventHandler):
    """
    Top level file handling class extending Watchdogs
    PatternMatchingEventHandler object.
    """

    def __init__(self, img_lst=None):
        """
        Initialisation of FileWatchTop class
        Inits the PatterMatchingEventHandler from Watchdogs
        Creates an empty list of images and creates
        an OctoWatch instance.

        Args:
            img_lst (list) - current list of images
        """
        PatternMatchingEventHandler.__init__(self,
                                             patterns=["*.jpg"],
                                             ignore_directories=True,
                                             case_sensitive=False)
        self.path_lst = img_lst

    def set_path_lst(self, lst):
        self.path_lst = lst

    def correct_path(self, old_path):
        """
        Being provided with a file path, the function
        removes the .jpg.* extension and fixes a . found
        in the path. It then returns path with the .jpg
        extension added.

        Args:
            old_path (str) - the file path provided to be corrected

        Returns:
            str: the cleaned path
        """
        dir_path = re.search('(.*/)', old_path).group()
        path = re.sub('(.jpg.*$)', '', old_path)
        path = re.sub('((?<=\/)[\.-])', '', path)
        path = path + ".jpg"
        return path

    def get_path(self, event):
        """
        If the event type is 'moved' which is the case
        using RSYNC and SSH, then correct the path
        and return the fixed version.

        Args:
            event (Event) - a file event

        Returns:
            str: src path to the event file
        """
        path = ""
        if event.event_type == 'moved' or event.event_type == 'created':
            path = self.correct_path(event.src_path)
        return path

    def process(self, event):
        """
        Process function which is run after each
        event.

        Args:
            event (Event) - a file event
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        if self.path_lst == []:
            self.path_lst.append(event.src_path)
        else:
            if event.src_path != self.path_lst[-1]:
                self.path_lst.append(event.src_path)

    def on_modified(self, event):
        """
        Using watchdogs checks if file has been modified.

        Args:
            event (Event) - a file event
        """
        self.process(event)

    def on_created(self, event):
        """
        Using watchdogs checks if file has been created.

        Args:
            event (Event) - a file event
        """
        self.process(event)

    def on_moved(self, event):
        """
        Using watchdogs checks if file has been moved.

        Args:
            event (Event) - a file event
        """
        self.process(event)

    def on_deleted(self, event):
        """
        Using watchdogs checks if file has been deleted.

        Args:
            event (Event) - a file event
        """
        self.process(event)
