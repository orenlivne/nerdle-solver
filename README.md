# Nerdle Solver
A fast algorithm for solving [Nerdle](https://nerdlegame.com) with various slot sizes.
Mini Nerdle = 6 slots. Nerdle = 8 slots.

## Prerequisites
* Install C++ compiler (`gcc`; if different, modify the `CC` variable in Makefile` accordingly.)
* Install `conda` (`miniconda` is sufficient).

## Installation
* Clone the git repo.
* Install the environment: `conda env create --file environment.yml -n nerdle`
* Activate the environment: `conda activate nerdle`
* Run `cd src/nerle && make`.
* Add `src` to your `PYTHONPATH` environment variable.

## Running Unit Tests
* Run `pytest test` in the root project directory.

## Resources
* https://betterprogramming.pub/solving-mastermind-641411708d01
* https://github.com/starypatyk/nerdle-solver
* https://www.youtube.com/watch?v=Okm_t5T1PiA&ab_channel=Confreaks
* https://www.youtube.com/watch?v=v68zYyaEmEA&ab_channel=3Blue1Brown
* New MIT Werdle Dynamic Programming Solver: https://auction-upload-files.s3.amazonaws.com/Wordle_Paper_Final.pdf .
  Possibly applicable to Nerdle.

## Contact
Oren Livne <oren.livne@gmail.com>
