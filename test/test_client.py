"""Nerdle web client tests."""
import os.path

import numpy as np
import pytest
from selenium import webdriver
from numpy.testing import assert_array_equal

import nerdle
import nerdle.client
from nerdle.score import score_to_hint_string
from nerdle.client import NUM_SLOTS, MAX_GUESSES

SCORE_DB_MATRIX_FILE = os.path.join(nerdle.DB_DIR, "nerdle{}.db".format(NUM_SLOTS))


@pytest.fixture()
def solver_data():
    os.makedirs(os.path.dirname(SCORE_DB_MATRIX_FILE), exist_ok=True)
    return nerdle.solver.create_solver_data(NUM_SLOTS, SCORE_DB_MATRIX_FILE)


class TestClient:
    def setup_method(self, method):
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
        self.client = nerdle.client.NerdleClient(driver)

    def teardown_method(self, method):
        self.client.__exit__(None, None, None)

    def test_play_game(self, solver_data):
        # Answer taken from the Nerdle archive:
        # https://www.dexerto.com/gaming/daily-nerdle-answers-todays-nerdle-equation-1836105/
        solver = nerdle.solver.NerdleSolver(solver_data)
        success, guess_history, hint_history = self.client.play_game(
            solver, "https://nerdlegame.com/20220913", live=False)
        assert success
        assert guess_history == ['9*8-7=65', '14+18=32', '2+1+8=11']
        assert [
            score_to_hint_string(
                hint,
                NUM_SLOTS) for hint in hint_history] == [
            '--?--+--',
            '?-??++-?',
            '++++++++']

    def test_live_game(self, solver_data):
        solver = nerdle.solver.NerdleSolver(solver_data)
        success, guess_history, hint_history = self.client.play_game(
            solver, "https://nerdlegame.com", live=True)
        assert success
        assert len(guess_history) <= 4
