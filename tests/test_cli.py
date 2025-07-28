import subprocess
import sys
import os
import pandas as pd

SRC_DIR = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, SRC_DIR)

from doe_python.cli import main


def test_cli_factorial(tmp_path):
    output = tmp_path / "design.csv"
    args = [
        "factorial",
        "-f",
        "A=0,1",
        "-f",
        "B=0,1",
        "-r",
        "1",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert len(df) == 4
    assert set(df.columns).issuperset({"A", "B"})
