import os
from os.path import dirname, abspath
d = dirname(dirname(abspath(__file__))) # /home/kristina/desire-directory

DB_DIR = os.path.join(dirname(dirname(dirname(abspath(__file__)))), "db")

from . import score, solver, analysis
