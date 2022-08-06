import os
import re
from collections import OrderedDict
import numpy as np
import pandas as pd
import pathlib
import spotpy

import definitions
from hydromodel.utils import hydro_utils


def mm_per_day_to_m3_per_sec(basin_area, q):
    """
    trans mm/day to m3/s for xaj models

    Parameters
    ----------
    basin_area
        we need to know the area of a basin so that we can perform this transformation
    q
        original streamflow data

    Returns
    -------

    """
    # 1 ft3 = 0.02831685 m3
    # ft3tom3 = 2.831685e-2
    # 1 km2 = 10^6 m2
    km2tom2 = 1e6
    # 1 m = 1000 mm
    mtomm = 1000
    # 1 day = 24 * 3600 s
    daytos = 24 * 3600
    q_trans = q * basin_area * km2tom2 / (mtomm * daytos)
    return q_trans


def save_sceua_calibrated_params(basin_id, sceua_calibrated_file_name):
    """

    Parameters
    ----------
    basin_id
        one basin's id
    sceua_calibrated_file_name
        the parameters' file generated by spotpy SCE-UA when finishing calibration

    Returns
    -------

    """
    results = spotpy.analyser.load_csv_results(sceua_calibrated_file_name)
    bestindex, bestobjf = spotpy.analyser.get_minlikeindex(results)
    best_model_run = results[bestindex]
    fields = [word for word in best_model_run.dtype.names if word.startswith("par")]
    best_calibrate_params = pd.DataFrame(list(best_model_run[fields]))
    save_dir = os.path.join("..", "example", basin_id)
    save_file = os.path.join(save_dir, basin_id + "_calibrate_params.txt")
    best_calibrate_params.to_csv(save_file, sep=',', index=False, header=True)
    return np.array(best_calibrate_params).reshape(1, -1)


def summarize_parameters(path):
    """
    output parameters of all basins to one file

    Parameters
    ----------
    path

    Returns
    -------

    """
    path = pathlib.Path(path)
    all_basins_files = [file for file in path.iterdir() if file.is_dir()]
    params = []
    for i in all_basins_files:
        columns = ["k", "B", "IM", "UM", "LM", "DM", "C", "SM", "EX", "KI", "KG", "A", "THETA", "CI", "CG"]
        basin_id = ["60650", "60668", "61239", "61277", "61561", "61716", "62618", "63002",
                    "63007", "63486", "63490", "90813", "92353", "92354", "94470", "94560", "94850", "95350"]
        basin_area = ['14818.483', '4481.933', '3385.442', '1771.092', '8750.786', '14645.912', '11874.102', '7917.104',
                      '3190.371', '1250.674', '1458.503', '2610.43',
                      '12931.5138', '2395.8437', '9413.55', '4366.523', '4874.683', '10954.025']
        basin_files = os.listdir(os.path.join("example", i))
        # print(basin_files)
        params_txt = pd.read_csv(os.path.join("example", i, basin_files[6]))
        params_df = pd.DataFrame(params_txt.values.T, columns=columns)
        params.append(params_df)
    params_dfs = pd.concat(params, axis=0)
    params_dfs.index = basin_id
    # params_dfs["basin"] =  basin_id
    # params_dfs["basin_area"]=basin_area
    print(params_dfs)
    params_dfs_ = params_dfs.transpose()
    params_npy_file = os.path.join(
        definitions.ROOT_DIR, "result", "MZ", "basins_params.npy"
    )
    hydro_utils.serialize_numpy(params_dfs_, params_npy_file)
    data = hydro_utils.unserialize_numpy(params_npy_file)
    np.testing.assert_array_equal(data, params_dfs_)


def renormalization_params_CSL(path):
    path = pathlib.Path(path)
    all_basins_files = [file for file in path.iterdir() if file.is_dir()]
    renormalization_params = []
    for i in all_basins_files:
        basin_files = os.listdir(os.path.join("example", i))
        # print(basin_files)
        params = np.loadtxt(os.path.join("example", i, basin_files[6]))[1:].reshape(1, 15)
        param_ranges = OrderedDict(
            {
                "K": [0.5, 2.0],
                "B": [0.1, 0.4],
                "IM": [0.01, 0.1],
                "UM": [0.0, 20.0],
                "LM": [60.0, 90.0],
                "DM": [60.0, 120.0],
                "C": [0.0, 0.2],
                "SM": [1, 100.0],
                "EX": [1.0, 1.5],
                "KI": [0.0, 0.7],
                "KG": [0.0, 0.7],
                "CS": [0.0, 1.0],
                "L": [1.0, 10.0],  # unit is day
                "CI": [0.0, 0.9],
                "CG": [0.98, 0.998],
            }
        )
        xaj_params = [
            (value[1] - value[0]) * params[:, i] + value[0]
            for i, (key, value) in enumerate(param_ranges.items())
        ]
        k = xaj_params[0]
        b = xaj_params[1]
        im = xaj_params[2]
        um = xaj_params[3]
        lm = xaj_params[4]
        dm = xaj_params[5]
        c = xaj_params[6]
        sm = xaj_params[7]
        ex = xaj_params[8]
        ki = xaj_params[9]
        kg = xaj_params[10]
        # ki+kg should be smaller than 1; if not, we scale them
        ki = np.where(ki + kg < 1.0, ki, 1 / (ki + kg) * ki)
        kg = np.where(ki + kg < 1.0, kg, 1 / (ki + kg) * kg)
        cs = xaj_params[11]
        l = xaj_params[12]
        ci = xaj_params[13]
        cg = xaj_params[14]
        xaj_params_dict = {
            "K": k,
            "B": b,
            "IM": im,
            "UM": um,
            "LM": lm,
            "DM": dm,
            "C": c,
            "SM": sm,
            "EX": ex,
            "KI": ki,
            "KG": kg,
            "CS": cs,
            "L": l,  # unit is day
            "CI": ci,
            "CG": cg,
        }
        xaj_params_array = [value
                            for i, (key, value) in enumerate(xaj_params_dict.items())
                            ]
        xaj_params_ = np.array([x for j in xaj_params_array for x in j])
        params_df = pd.DataFrame(xaj_params_.T)
        renormalization_params.append(params_df)
    renormalization_params_dfs = pd.concat(renormalization_params, axis=1)
    print(renormalization_params_dfs)
    # params_dfs_ =renormalization_params_dfs.transpose()
    params_npy_file = os.path.join(
        definitions.ROOT_DIR, "result", "CSL", "basins_renormalization_params.npy"
    )
    hydro_utils.serialize_numpy(renormalization_params_dfs, params_npy_file)
    data = hydro_utils.unserialize_numpy(params_npy_file)
    np.testing.assert_array_equal(data, renormalization_params_dfs)


def renormalization_params_MZ(path):
    path = pathlib.Path(path)
    all_basins_files = [file for file in path.iterdir() if file.is_dir()]
    renormalization_params = []
    for i in all_basins_files:
        basin_files = os.listdir(os.path.join("example", i))
        # print(basin_files)
        params = np.loadtxt(os.path.join("example", i, basin_files[6]))[1:].reshape(1, 15)
        param_ranges = OrderedDict(
            {
                "K": [0.5, 2.0],
                "B": [0.1, 0.4],
                "IM": [0.01, 0.1],
                "UM": [0.0, 20.0],
                "LM": [60.0, 90.0],
                "DM": [60.0, 120.0],
                "C": [0.0, 0.2],
                "SM": [1, 100.0],
                "EX": [1.0, 1.5],
                "KI": [0.0, 0.7],
                "KG": [0.0, 0.7],
                "A": [0.0, 2.9],
                "THETA": [0.0, 6.5],
                "CI": [0.0, 0.9],
                "CG": [0.98, 0.998],
            }
        )
        xaj_params = [
            (value[1] - value[0]) * params[:, i] + value[0]
            for i, (key, value) in enumerate(param_ranges.items())
        ]
        k = xaj_params[0]
        b = xaj_params[1]
        im = xaj_params[2]
        um = xaj_params[3]
        lm = xaj_params[4]
        dm = xaj_params[5]
        c = xaj_params[6]
        sm = xaj_params[7]
        ex = xaj_params[8]
        ki = xaj_params[9]
        kg = xaj_params[10]
        # ki+kg should be smaller than 1; if not, we scale them
        ki = np.where(ki + kg < 1.0, ki, 1 / (ki + kg) * ki)
        kg = np.where(ki + kg < 1.0, kg, 1 / (ki + kg) * kg)
        a = xaj_params[11]
        theta = xaj_params[12]
        ci = xaj_params[13]
        cg = xaj_params[14]
        xaj_params_dict = {
            "K": k,
            "B": b,
            "IM": im,
            "UM": um,
            "LM": lm,
            "DM": dm,
            "C": c,
            "SM": sm,
            "EX": ex,
            "KI": ki,
            "KG": kg,
            "A": a,
            "THETA": theta,
            "CI": ci,
            "CG": cg,
        }
        xaj_params_array = [value
                            for i, (key, value) in enumerate(xaj_params_dict.items())
                            ]
        xaj_params_ = np.array([x for j in xaj_params_array for x in j])
        params_df = pd.DataFrame(xaj_params_.T)
        renormalization_params.append(params_df)
    renormalization_params_dfs = pd.concat(renormalization_params, axis=1)
    print(renormalization_params_dfs)
    params_npy_file = os.path.join(
        definitions.ROOT_DIR, "result", "MZ", "basins_renormalization_params.npy"
    )
    hydro_utils.serialize_numpy(renormalization_params_dfs, params_npy_file)
    data = hydro_utils.unserialize_numpy(params_npy_file)
    np.testing.assert_array_equal(data, renormalization_params_dfs)


def summarize_metrics(path):
    """
    output all results' metrics of all basins to one file

    Parameters
    ----------
    path

    Returns
    -------

    """
    path = pathlib.Path(path)
    # all_basins_files = os.listdir(path)
    all_basins_files = [file for file in path.iterdir() if file.is_dir()]
    zhibiaos = []
    for i in all_basins_files:
        basin_files = os.listdir(os.path.join("example", i))
        zhibiao_txt = pd.read_csv(os.path.join("example", i, basin_files[9]), sep=",", header=None)
        zhibiao = []
        for j in range(zhibiao_txt.shape[1]):
            basin_zhibiao = float(re.findall(r'[[](.*?)[]]', zhibiao_txt[j][0])[0])
            zhibiao.append(basin_zhibiao)
        zhibiaos.append(zhibiao)
    basin_id = ["60650", "60668", "61239", "61277", "61561", "61716", "62618", "63002",
                "63007", "63486", "63490", "90813", "92353", "92354", "94470", "94560", "94850", "95350"]
    basin_area = ['14818.483', '4481.933', '3385.442', '1771.092', '8750.786', '14645.912', '11874.102', '7917.104',
                  '3190.371', '1250.674', '1458.503', '2610.43',
                  '12931.5138', '2395.8437', '9413.55', '4366.523', '4874.683', '10954.025']
    columns = ["Bias", "RMSE", "ubRMSE", "Corr", "R2", "NSE", "KGE", "FHV", "FLV"]
    zhibiao_dfs = pd.DataFrame(zhibiaos, columns=columns, index=basin_id)
    zhibiao_dfs["basin"] = basin_id
    zhibiao_dfs["basin_area"] = basin_area
    # print(zhibiao_dfs)
    zhibiao_dfs_ = zhibiao_dfs[zhibiao_dfs["NSE"] > 0]
    print(zhibiao_dfs_)
    print(zhibiao_dfs_["NSE"].median())
    print(zhibiao_dfs_["NSE"].mean())
    # zhibiao_dfs_=zhibiao_dfs.transpose()
    # index_npy_file=os.path.join(
    #     definitions.ROOT_DIR, "result", "MZ", "basins_index.npy"
    # )
    # hydro_utils.serialize_numpy(zhibiao_dfs_, index_npy_file)
    # data = hydro_utils.unserialize_numpy(index_npy_file)
    # np.testing.assert_array_equal(data, zhibiao_dfs_)


def save_streamflow_to_npy_file(path):
    path = pathlib.Path(path)
    all_basins_files = [file for file in path.iterdir() if file.is_dir()]
    streamflow = []
    for i in all_basins_files:
        basin_files = os.listdir(os.path.join("example", i))
        # print(basin_files)
        streamflow_txt = pd.read_csv(os.path.join("example", i, basin_files[9]))
        streamflow_df = pd.DataFrame(streamflow_txt.values)
        streamflow.append(streamflow_df)
    streamflow_dfs = pd.concat(streamflow, axis=1)[1:]
    # params_dfs.index=basin_id
    # # params_dfs["basin"] =  basin_id
    # # params_dfs["basin_area"]=basin_area
    print(streamflow_dfs)
    # params_dfs_ = params_dfs.transpose()
    eva_npy_file = os.path.join(
        definitions.ROOT_DIR, "result", "MZ", "basin_qsim.npy"
    )
    hydro_utils.serialize_numpy(streamflow_dfs, eva_npy_file)
    data = hydro_utils.unserialize_numpy(eva_npy_file)
    np.testing.assert_array_equal(data, streamflow_dfs)
