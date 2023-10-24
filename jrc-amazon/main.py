import glob
import os
from functools import partial
import json

import geopandas as gpd
import numpy as np
from osgeo import gdal # type: ignore
import matplotlib.pyplot as plt

from yirgacheffe.layers import RasterLayer, TiledGroupLayer, VectorLayer

# Convert Amazon Basin to GeoJSON
amazon_geojson_path = "./amazon.geojson"
amazon_basin = gpd.read_file("./amazon/amapoly_ivb.shp")
amazon_basin.to_file(amazon_geojson_path, driver='GeoJSON')

def update_counts(
    counts,
    arr
):
    bins = np.bincount(arr)
    for i in range(len(bins)):
        if i == 0:
            continue
        else:
            counts[i] = counts[i] + bins[i]

def compute_proportions(
    jrc_directory_paths: str,
    luc_years: [str]
):
    results = {}
    for jrc_directory_path in jrc_directory_paths:
        if jrc_directory_path not in results:
            results[jrc_directory_path] = {}
        for year in luc_years:
            print(f"Calculating proporitions for {jrc_directory_path} in year {year}")
            lucs = TiledGroupLayer([
                RasterLayer.layer_from_file(os.path.join(jrc_directory_path, filename)) for filename in
                    glob.glob(f"*{year}*.tif", root_dir=jrc_directory_path)
            ], name=f"luc_{year}")

            # Read Amazon basin into yirgacheffe
            amazon = VectorLayer.layer_from_file(
                amazon_geojson_path,
                None,
                lucs.pixel_scale,
                lucs.projection
            )

            # Intersect LUC with Amazon basin
            intersection = RasterLayer.find_intersection([lucs, amazon])
            lucs.set_window_for_intersection(intersection)
            amazon.set_window_for_intersection(intersection)

            result = RasterLayer.empty_raster_layer(
                intersection,
                lucs.pixel_scale,
                gdal.GDT_Byte,
                "/maps/pf341/tmp/result.tif",
                lucs.projection
            )

            calc = lucs * amazon
            calc.save(result)

            counts = np.array([0, 0, 0, 0, 0, 0, 0])

            for yoffset in range(result.window.ysize):
                row_lucs = result.read_array(0, yoffset, result.window.xsize, 1)[0]
                update_counts(counts, row_lucs)
            counts = counts[1:]
            proportions = counts / counts.sum()
            results[jrc_directory_path][year] = proportions.tolist()
    s = json.dumps(results)
    with open("./results.json", "w+") as f:
        f.write(s)

# Replace with paths to JRC versions.
jrcs = [
    "/maps/forecol/data/JRC/AnnualChange/tifs",
    "/maps/forecol/data/JRC/v1_2022/AnnualChange/tifs",
]

# Replace with years you are interested in.
years = [ 2015, 2016, 2017, 2018, 2019, 2020 ]

def compute():
    compute_proportions(jrcs, years)

def graph():
    with open("./results.json", "r") as f:
        results = json.load(f)

    res2021 = results[jrcs[0]]
    res2022 = results[jrcs[1]]

    fig, ax = plt.subplots(3, 2)

    fig.set_size_inches(10, 10)

    plt.suptitle("Proportion of LUCs in the Amazon Basin for different years and JRC datasets")

    colors = [ "#005a00", "#639b24", "#ff870f", "#d2fa3c", "#29d9e2", "#afafaf" ]

    ax[0][0].pie(res2021["2018"], colors=colors)
    ax[0][0].set_title("LUC 2018 (2021 JRC)")
    ax[0][1].pie(res2022["2018"], colors=colors)
    ax[0][1].set_title("LUC 2018 (2022 JRC)")

    ax[1][0].pie(res2021["2019"], colors=colors)
    ax[1][0].set_title("LUC 2019 (2021 JRC)")
    ax[1][1].pie(res2022["2019"], colors=colors)
    ax[1][1].set_title("LUC 2019 (2022 JRC)")

    ax[2][0].pie(res2021["2020"], colors=colors)
    ax[2][0].set_title("LUC 2020 (2021 JRC)")
    ax[2][1].pie(res2022["2020"], colors=colors)
    ax[2][1].set_title("LUC 2020 (2022 JRC)")

    fig.legend(["Undisturbed", "Degraded", "Deforested", "Regrowth", "Water", "Other"])

    res2021_2020 = np.around(np.array(res2021["2020"]) * 100, decimals=2)
    res2022_2020 = np.around(np.array(res2022["2020"]) * 100, decimals=2)

    print(res2021_2020)
    print(res2022_2020)
    print(res2022_2020 - res2021_2020)
    print(((res2022_2020 - res2021_2020) * 100).sum())

    fig.savefig("./data.png")

# Call either compute() or graph()