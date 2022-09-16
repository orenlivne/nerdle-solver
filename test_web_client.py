"""The first time this test is run, it builds the 8-slot Nerdle solver database, which takes several minutes. Subsequent
test run times should be in the few seconds."""
import numpy as np
import pytest
from selenium import webdriver
from numpy.testing import assert_array_equal

import nerdle
import web_client
from web_client import NUM_SLOTS, MAX_GUESSES

SCORE_DB_MATRIX_FILE = "db/nerdle{}.db".format(web_client.NUM_SLOTS)


@pytest.fixture()
def solver_data():
    return nerdle.create_solver_data(NUM_SLOTS, SCORE_DB_MATRIX_FILE)


class TestWebClient:
    def setup_method(self, method):
        options = webdriver.ChromeOptions()
        for option in ("headless", "disable-gpu", "window-size=1920,1080", "ignore-certificate-errors",
                       "no-sandbox", "disable-dev-shm-usage"):
            options.add_argument(option)
        driver = webdriver.Chrome(options=options)
        self.client = web_client.NerdleClient(driver)

    def teardown_method(self, method):
        self.client.__exit__(None, None, None)

    def test_play_game(self, solver_data):
        # Answer taken from the Nerdle archive:
        # https://www.dexerto.com/gaming/daily-nerdle-answers-todays-nerdle-equation-1836105/
        self._play_archived_game(solver_data, "https://nerdlegame.com/20220913", "2+1+8=11")

    def _play_archived_game(self, solver_data, url, answer):
        # First, play the game with the known answer to know what hints we expect to get from the website.
        solver = nerdle.NerdleSolver(solver_data)
        guess_history, hint_history, _ = solver.solve(answer, initial_guess=web_client.INITIAL_GUESS)
        # Now play.
        self.client.load(url)
        grid = self.client.grid_values()
        self.client.print_grid(grid)
        assert_array_equal(grid[0], np.full((MAX_GUESSES, NUM_SLOTS), web_client.STATUS_STRING[web_client.EMPTY]))
        assert_array_equal(grid[1], np.full((MAX_GUESSES, NUM_SLOTS), web_client.EMPTY))
        self.client.print_grid(self.client.grid_values())
        guesses = [web_client.INITIAL_GUESS]
        for num_guesses, (expression, expected_hint) in enumerate(zip(guesses, hint_history), 1):
            for c in expression:
                self.client.insert(c)
            self.client.enter()

            grid = self.client.grid_values()
            self.client.print_grid(grid)
            assert_array_equal(grid[0],
                               [list(guess) for guess in guesses[:num_guesses]] +
                               [['.'] * NUM_SLOTS for _ in range(MAX_GUESSES - num_guesses)])
