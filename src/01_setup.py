"""
Section 1: Setup.

Installs dependencies and sets DATA_DIR, the folder every later script
reads/writes CSVs from. Run this first in any session.
"""

# Dependencies are listed in requirements.txt at the repo root:
#   pip install -r requirements.txt
# (The original notebook installed them inline via `!pip install ...` --
# that's Jupyter-magic syntax and isn't valid in a plain .py file.)

import os
import time
import random
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity


def data_path(filename):
    return os.path.join(DATA_DIR, filename)

# Original analysis ran in Colab with DATA_DIR pointed at a mounted Google
# Drive folder. Locally (or in this repo), just point it at a plain folder:
DATA_DIR = os.environ.get("SALAH_DATA_DIR", "./salah_replacement_data")
os.makedirs(DATA_DIR, exist_ok=True)

# If running in Colab and you want to persist to Drive instead, uncomment:
# from google.colab import drive
# drive.mount('/content/drive')
# DATA_DIR = "/content/drive/MyDrive/Football_Projects/salah_replacement"

print("Data will be cached to:", DATA_DIR)
