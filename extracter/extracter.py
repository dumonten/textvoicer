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
        return -1 while error
        -2 is not a time

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
