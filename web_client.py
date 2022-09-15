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


def parse_args():
    """Defines and parses command-line flags."""
    parser = argparse.ArgumentParser(description="Nerdle web client.")
    parser.add_argument("--path", required=True, help="nerdle website.")
    return parser.parse_args()


class NerdleClient:
    def __init__(self, driver):
        self._driver = driver
        self.square_elements, self.square_location, self.square_size = self.grid_square_location()

    def grid_square_location(self):
        "Returns grid square locations: row x column x (x, y)"
        try:
            WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'pb-grid')))
        except TimeoutException:
            raise TimeoutException("Loading took too much time!")

        square_elements = self._driver.find_elements("xpath", "//div[contains(@class, 'pb-grid')]//div[@role]")
        square_info = sorted((e.location['y'], e.location['x'], e.get_attribute("aria-label")) for e in square_elements)
        square_size = np.array([square_elements[0].size['width'], square_elements[0].size['height']])
        return np.array(square_elements).reshape(6, 8), \
               np.array([[x[0], x[1]] for x in square_info]).reshape(6, 8, 2), \
               square_size

    def grid_status(self):
        return np.array([[e.get_attribute("aria-label") for e in row] for row in self.square_elements])

    def write_text_in_square(self, row, col, text):
        action = webdriver.ActionChains(self._driver)
        # x, then y in move_by_offset. Move to middle of square, then send text.
        x, y = self.square_location[row, col] + self.square_size // 2
        print(x, y)
        action.move_by_offset(x, y).perform()
        action.send_keys(text)
        action.perform()


def _parse_state(score_str):
    # TODO(orenlivne): generalize parsing.
    return int(score_str.rstrip("pts").rstrip("m"))


if __name__ == "__main__":
    args = parse_args()

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(options=options)

    driver.get(args.path)
    client = NerdleClient(driver)

    print(client.square_location)
    print(client.square_size)
    print(client.grid_status())

    client.write_text_in_square(0, 0, "9")
    print(client.grid_status())
