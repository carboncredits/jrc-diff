import os
import argparse
from enum import IntEnum

import numpy as np
from osgeo import gdal
from yirgacheffe.layers import RasterLayer  # type: ignore

class LandUseClass(IntEnum):
    UNDISTURBED = 1
    DEGRADED = 2
    DEFORESTED = 3
    REGROWTH = 4
    WATER = 5
    OTHER = 6

# Create a dictionary to map pairings to unique values, 
# zero is treated as nothing
pairings = np.zeros((7, 7))
value = 1
for first_member in LandUseClass:
    for second_member in LandUseClass:
        pairings[first_member.value][second_member.value] = value
        value += 1

print(pairings)

def diff_luc(from_luc, to_luc):
    return pairings[from_luc][to_luc]

diff_luc = np.vectorize(diff_luc, otypes=[float])

def diff(
    older_jrc_dir,
    newer_jrc_dir,
    jrc_file,
    outdir,
    year_index
):
    print(f"Diffing file {jrc_file}")

    old_luc = RasterLayer.layer_from_file(os.path.join(older_jrc_dir, jrc_file))
    new_luc = RasterLayer.layer_from_file(os.path.join(newer_jrc_dir, jrc_file))

    # Work out the common subsection of all these and apply it to the layers
    intersection = RasterLayer.find_intersection([old_luc, new_luc])
    old_luc.set_window_for_intersection(intersection)
    new_luc.set_window_for_intersection(intersection)

    result = RasterLayer.empty_raster_layer(
        intersection,
        old_luc.pixel_scale,
        gdal.GDT_Int16,
        os.path.join(outdir, jrc_file),
        old_luc.projection
    )

    # TODO: Yirgacheffe was sometimes off by one here, so manually set.
    result.set_window_for_intersection(intersection)

    print("Diffing and saving...")
    diff_lucs = old_luc.numpy_apply(diff_luc, new_luc)
    # diff_lucs = old_luc - new_luc
    diff_lucs.save(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Diff two JRC datasets for a particular year..."
    )
    parser.add_argument(
        "--older",
        type=str,
        required=True,
        dest="older",
        help="The older JRC dataset directory.",
    )
    parser.add_argument(
        "--newer",
        type=str,
        required=True,
        dest="newer",
        help="The newer JRC dataset directory.",
    )
    parser.add_argument(
        "--jrc-filename",
        type=str,
        required=True,
        dest="jrc_filename",
        help="Filename in the dir to diff.",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        required=True,
        dest="outdir",
        help="The output directory for the difference data.",
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        dest="year",
        help="The year to diff.",
    )

    args = parser.parse_args()

    diff(args.older, args.newer, args.jrc_filename, args.year)