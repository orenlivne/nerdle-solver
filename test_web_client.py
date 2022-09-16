# Generated by Selenium IDE
import numpy as np
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from score import OPERATIONS, EQUALS

# Send an expression.
ENTER = "ENTER"
# List of standardized button labels representing all game operations.
SYMBOLS = set([str(i) for i in range(10)] + list(OPERATIONS) + [EQUALS, ENTER])


class TestWebClient:
    def setup_method(self, method):
        # self.driver = webdriver.Chrome()
        options = webdriver.ChromeOptions()
        for option in ("headless", "disable-gpu", "window-size=1920,1080", "ignore-certificate-errors",
                       "no-sandbox", "disable-dev-shm-usage"):
            options.add_argument(option)
        self.driver = webdriver.Chrome(options=options)
        #self.driver.set_window_size(1197, 710)
        self.driver.maximize_window()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_button(self):
        self.driver.get("https://nerdlegame.com/20220913")
        self.wait_for_page_load()
        self.print_grid()
        button_elements = self.driver.find_elements("xpath", "//button")
        buttons = dict((parse_button_label(x), x) for x in button_elements)
        b = self.driver.find_element(By.XPATH, "//div[@id='root']/div/div[2]/div[2]/div[3]/div/button")
        for c in "9*8-7=65":
            self.click(buttons[c])
        self.click(buttons[ENTER])
        self.print_grid()

    def click(self, button):
        self.driver.execute_script("arguments[0].click();", button)

    def print_grid(self):
        print("\n".join("".join(row) for row in self.grid_values()))

    def wait_for_page_load(self):
        try:
            WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'pb-grid')))
        except TimeoutException:
            raise TimeoutException("Loading took too much time!")

    def grid_values(self):
        square_elements = self.driver.find_elements("xpath", "//div[contains(@class, 'pb-grid')]//div[@role]")
        square_elements = np.array(square_elements).reshape(6, 8)
        return np.array([[parse_square_value(e.get_attribute("aria-label")) for e in row] for row in square_elements])


def parse_button_label(element):
    return parse_label(element.get_attribute("aria-label"))


def parse_label(label):
    return label.strip().replace("minus", "-")


def parse_square_value(label):
    label = label.strip().split(" ")[0].lower()
    if label == "undefined":
        return "."
    if label in SYMBOLS:
        return label
    return "?"
