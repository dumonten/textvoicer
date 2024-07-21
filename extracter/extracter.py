import select
import subprocess

from loguru import logger


class Extracter:

    def __init__(self, nbuff=10):
        self._buffer = []
        self._nbuff = nbuff

    def _clear(self):
        self._buffer.clear()

    def _cond_clear(self):
        if len(self._buffer) > self._nbuff:
            self._buffer.clear()

    def _check_with(self, text, top=3):
        return len(self._buffer) >= top and all(
            [text == t for t in self._buffer[-top:]]
        )

    def get_selected_text(self):
        """
        Function that retrieves the currently highlighted text.
        It works is exclusively for Linux users and requires the prior installation of xclip.

        Returns:
        - Text (str): This returns the highlighted text.
        - Error Code (int): In case of an error, it returns a negative integer value. Here's what the codes mean:
            (-1) indicates an internal error.
            (-2) suggests a need to confirm whether to voice the selected text.
        """

        text = ""
        try:
            text = subprocess.check_output(
                "xclip -selection primary -out", shell=True
            ).decode("utf-8")
        except Exception as e:
            logger.error(f"An error occurred while extracting the text: {e}")
            return -1

        if len(text):
            self._cond_clear()
            self._buffer.append(text)
            if not self._check_with(text, top=5):
                return -2
        return text
