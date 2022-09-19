#!/usr/bin/env python
"""Downloads human benchmark data using Selenium."""
import argparse
import numpy as np
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import nerdle
from score import OPERATIONS, EQUALS, Hint, HINT_STRING, hints_to_score, score_to_hint_string


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
INITIAL_GUESS = "9*8-7=65"

BUTTON_LABEL_TO_HINT = {
    "absent": Hint.ABSENT,
    "present": Hint.PRESENT,
    "correct": Hint.CORRECT}
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
        self._actions = dict((_parse_button_label(x), x)
                             for x in button_elements)

    def exit_welcome_screen(self):
        close_button = [
            x for x in self._driver.find_elements(
                "xpath",
                "//button[@aria-label='Home'][*[local-name() = 'svg']]") if x.get_attribute("class") == "focus:outline-none"][0]
        self._click(close_button)

    def input_guess(self, guess):
        for c in guess:
            self._insert(c)
        self._insert(ENTER)

    def grid_values(self):
        square_elements = self._driver.find_elements(
            "xpath", "//div[contains(@class, 'pb-grid')]//div[@role]")
        square_elements = np.array(square_elements).reshape(6, 8)
        info = [[_parse_square(e.get_attribute(SQUARE_ATTRIBUTE))
                 for e in row] for row in square_elements]
        value = np.array([[x[0] for x in row] for row in info])
        status = np.array([[x[1] for x in row] for row in info], dtype=int)
        return value, status

    def print_grid(self, grid_values):
        value, status = grid_values
        print("\n".join("".join(row) for row in value))
        print("\n".join("".join(map(STATUS_STRING.get, row))
              for row in status))

    def play_game(self, solver, url, live: bool = True):
        self.load(url)
        if live:
            self.exit_welcome_screen()
        hint_generator = _NerdleWebHintGenerator(self)

        guess = INITIAL_GUESS
        guesses_left = MAX_GUESSES
        hint_history = []
        guess_history = [guess]
        guess_key = solver.guess_key(guess)
        success = False
        while guesses_left > 0:
            guesses_left -= 1
            score = hint_generator(guess)
            hint_history.append(score)
            if solver.is_correct(score):
                success = True
                break
            guess_key = solver.make_guess(guess_key, score)
            guess = solver.guess_value(guess_key)
            if guess is not None:
                guess_history.append(guess)
        return success, guess_history, hint_history

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


class _NerdleWebHintGenerator:
    def __init__(self, client):
        self._guess_num = 0
        self._client = client

    def __call__(self, guess: str):
        self._client.input_guess(guess)
        grid = self._client.grid_values()
        hint = hints_to_score(grid[1][self._guess_num])
        self._guess_num += 1
        return hint


def _parse_button_label(element):
    return element.get_attribute(
        SQUARE_ATTRIBUTE).strip().replace("minus", "-")


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
        # Nothing to do here, value string is the desired output, e.g., "1" or
        # "+".
        pass
    else:
        value = "?"

    return value, status


def parse_args():
    """Defines and parses command-line flags."""
    parser = argparse.ArgumentParser(description="Nerdle web client.")
    parser.add_argument(
        "--path",
        required=True,
        help="Nerdle game website URL.")
    parser.add_argument(
        "--score_db",
        default="db/nerdle8.db",
        help="Path to score database file name.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    options = webdriver.ChromeOptions()
    for option in (
        "headless",
        "disable-gpu",
        "window-size=1920,1080",
        "ignore-certificate-errors",
        "no-sandbox",
            "disable-dev-shm-usage"):
        options.add_argument(option)
    driver = webdriver.Chrome(options=options)

    os.makedirs(os.path.dirname(args.score_db), exist_ok=True)
    solver_data = nerdle.create_solver_data(NUM_SLOTS, args.score_db)

    client = NerdleClient(driver)
    solver = nerdle.NerdleSolver(solver_data)
    success, guess_history, hint_history = client.play_game(
        solver, "https://nerdlegame.com", live=True)

    print(
        "Game result: {}, {} guesses".format(
            "Success! :)" if success else "Failure :(",
            len(guess_history)))
    for guess, hint in zip(guess_history, hint_history):
        print("{} {}".format(guess, score_to_hint_string(hint, NUM_SLOTS)))
