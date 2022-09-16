#!/usr/bin/env python
"""Downloads human benchmark data using Selenium."""
import argparse
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from score import OPERATIONS, EQUALS, Hint, HINT_STRING


# Send an expression.
ENTER = "ENTER"
# List of standardized button labels representing all game operations.
SYMBOLS = set([str(i) for i in range(10)] + list(OPERATIONS) + [EQUALS, ENTER])
# A hint code that is not needed for the Nerdle game rules, but useful for the web interface Client: an empty
# square in the Nerdle grid. hint codes are 0..2 so set this to 3.
EMPTY = 3

# Game grid size.
NUM_SLOTS = 8
MAX_GUESSES = 6
# We use a fixed initial guess to play.
INITIAL_GUESS="9*8-7=65"

BUTTON_LABEL_TO_HINT = {"absent": Hint.ABSENT, "present": Hint.PRESENT, "correct": Hint.CORRECT}
STATUS_STRING = dict(list(HINT_STRING.items()) + [(EMPTY, ".")])


SQUARE_ATTRIBUTE = "aria-label"


class NerdleClient:
    def __init__(self, driver):
        self._driver = driver
        self._actions = None

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._driver.quit()

    def load(self, url):
        self._driver.get(url)
        self._wait_for_page_load()
        button_elements = self._driver.find_elements("xpath", "//button")
        self._actions = dict((_parse_button_label(x), x) for x in button_elements)

    def input_guess(self, guess):
        for c in guess:
            self._insert(c)
        self._insert(ENTER)

    def grid_values(self):
        square_elements = self._driver.find_elements("xpath", "//div[contains(@class, 'pb-grid')]//div[@role]")
        square_elements = np.array(square_elements).reshape(6, 8)
        info = [[_parse_square(e.get_attribute(SQUARE_ATTRIBUTE)) for e in row] for row in square_elements]
        value = np.array([[x[0] for x in row] for row in info])
        status = np.array([[x[1] for x in row] for row in info], dtype=int)
        return value, status

    def print_grid(self, grid_values):
        value, status = grid_values
        print("\n".join("".join(row) for row in value))
        print("\n".join("".join(map(STATUS_STRING.get, row)) for row in status))

    def _wait_for_page_load(self):
        try:
            WebDriverWait(self._driver, 1).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'pb-grid')))
        except TimeoutException:
            raise TimeoutException("Loading took too much time!")

    def _insert(self, symbol):
        self._click(self._actions[symbol])

    def _click(self, button):
        self._driver.execute_script("arguments[0].click();", button)


def _parse_button_label(element):
    return element.get_attribute(SQUARE_ATTRIBUTE).strip().replace("minus", "-")


def _parse_square(label):
    """Returns the value and status (hint) of a square."""
    parts = label.strip().split(" ")
    if len(parts) == 1:
        value = parts[0]
        status = EMPTY
    else:
        value, status = parts
        try:
            status = BUTTON_LABEL_TO_HINT[status]
        except KeyError:
            status = EMPTY

    if value == "undefined":
        value = "."
    elif value in SYMBOLS:
        # Nothing to do here, value string is the desired output, e.g., "1" or "+".
        pass
    else:
        value = "?"

    return value, status


def parse_args():
    """Defines and parses command-line flags."""
    parser = argparse.ArgumentParser(description="Nerdle web client.")
    parser.add_argument("--path", required=True, help="nerdle website.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(options=options)

    driver.get(args.path)
    client = NerdleClient(driver)
