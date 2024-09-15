"""
Author: Wenyu Ouyang
Date: 2024-09-14 17:00:29
LastEditTime: 2024-09-14 17:25:16
LastEditors: Wenyu Ouyang
Description: Test the evaluate module
FilePath: \hydromodel\test\test_evaluate.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

import pandas as pd
import pytest
import xarray as xr
import numpy as np
from hydromodel.trainers.evaluate import Evaluator


@pytest.fixture
def sample_dataset():
    times = pd.date_range("2000-01-01", periods=10)
    basins = ["basin1", "basin2"]
    data = np.random.rand(10, 2)
    return xr.Dataset(
        {
            "prcp": (("time", "basin"), data),
            "pet": (("time", "basin"), data),
            "basin": (("basin",), basins),
            "time": (("time",), times),
        }
    )


def mock_read_yaml_config(file_path):
    # This function acts as a replacement for the real read_yaml_config
    # It returns a dummy configuration for the purposes of the test
    return {
        "data_type": "some_data_type",
        "data_dir": "path/to/data",
        "model": {"name": "xaj_mz"},
        "param_range_file": "param_range.yaml",
    }


@pytest.fixture
def evaluator(mocker):
    cali_dir = "path/to/cali_dir"
    param_dir = "path/to/param_dir"
    eval_dir = "path/to/eval_dir"

    # Mock os.path.exists to always return True
    mocker.patch("os.path.exists", return_value=True)

    # Mock os.makedirs to do nothing
    mocker.patch("os.makedirs")

    # Mock the read_yaml_config function inside the Evaluator class
    mocker.patch(
        "hydromodel.trainers.evaluate.read_yaml_config",
        side_effect=mock_read_yaml_config,
    )

    return Evaluator(cali_dir, param_dir, eval_dir)


def test_predict(sample_dataset, evaluator, mocker):
    # Mock the methods and functions used within predict
    mocker.patch(
        "hydromodel.trainers.evaluate._get_pe_q_from_ts",
        return_value=(sample_dataset, None),
    )
    mocker.patch(
        "hydromodel.trainers.evaluate._read_all_basin_params",
        return_value=np.random.rand(2, 10),
    )
    mocker.patch(
        "hydromodel.trainers.evaluate.MODEL_DICT",
        {
            "xaj_mz": lambda p_and_e, params, **kwargs: (
                sample_dataset,
                sample_dataset,
            )
        },
    )
    mocker.patch.object(
        Evaluator,
        "_convert_streamflow_units",
        return_value=(sample_dataset, sample_dataset),
    )

    qsim, qobs, etsim = evaluator.predict(sample_dataset)

    assert isinstance(qsim, xr.Dataset)
    assert isinstance(qobs, xr.Dataset)
    assert isinstance(etsim, xr.Dataset)
    assert "prcp" in qsim
    assert "prcp" in qobs
    assert "prcp" in etsim