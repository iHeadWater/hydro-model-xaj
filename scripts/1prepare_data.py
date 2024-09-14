"""
Author: Wenyu Ouyang
Date: 2024-03-25 09:21:56
LastEditTime: 2024-05-20 18:54:58
LastEditors: Wenyu Ouyang
Description: Script for preparing data
FilePath: \hydromodel\scripts\prepare_data.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

from pathlib import Path
import sys
import os
import argparse

current_script_path = Path(os.path.realpath(__file__))
repo_root_dir = current_script_path.parent.parent
sys.path.append(str(repo_root_dir))
from hydromodel.datasets.data_preprocess_topo import process_and_save_data_as_nc


def main(args):
    data_path = args.origin_data_dir

    if process_and_save_data_as_nc(data_path, save_folder=data_path, source='sql'):
        print("Data is ready!")
    else:
        print("Data format is incorrect! Please check the data.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare data.")
    parser.add_argument(
        "--origin_data_dir",
        type=str,
        help="Path to your hydrological data",
        default=r"C:\Users\Administrator\IdeaProjects\hydromodel-master\input",
    )

    args = parser.parse_args()
    main(args)
