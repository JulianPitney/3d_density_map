import zStackUtils as zsu
import Crop3D
import DensityMap3D
import config
import tifffile
import glob
from pathlib import Path
import cv2




# CROP AND CUBIFY
STACK_PATHS = glob.glob(config.SCANS_DIR + "*.tif")
CUBES_PATHS = []
AIVIA_RESULTS_PATHS = []
for path in STACK_PATHS:
    temp = Path(path)
    stem = temp.stem
    cubesPath = Path(config.SCANS_DIR + stem + "_cubes\\")
    excelPath = Path(config.SCANS_DIR + stem + "_excel\\")

    try:
        Path(cubesPath).mkdir(parents=False, exist_ok=False)
        Path(excelPath).mkdir(parents=False, exist_ok=False)
    except FileExistsError:
        print("FileExistsError. Directory creation failed.")
    except FileNotFoundError:
        print("FileNotFoundError. Directory creation failed.")
    except:
        print("UnknownError. Directory creation failed.")
    else:
        CUBES_PATHS.append(str(cubesPath) + "\\")
        AIVIA_RESULTS_PATHS.append(str(excelPath) + "\\")


for stackPath, cubesOutput in zip(STACK_PATHS, CUBES_PATHS):

    cropped = Crop3D.crop3D(stackPath)
    cubes = DensityMap3D.slice_into_cubes(cropped, config.CUBE_DIM_Z, config.CUBE_DIM_Y, config.CUBE_DIM_X)
    DensityMap3D.save_cubes_to_tif(cubes, cubesOutput)


# RUN THROUGH AIVIA
print("Pausing until Aivia excel results are in the folders...")
input("Press enter when ready")


# GENERATE DENSITY MAPS
for excelResPath, stackPath in zip(AIVIA_RESULTS_PATHS, STACK_PATHS):

    cubes = DensityMap3D.load_aivia_excel_results_into_cubes(excelResPath)
    DensityMap3D.map_path_lengths_to_range(cubes)
    stack = tifffile.imread(stackPath)
    temp = Path(path)
    stem = temp.stem

    for cube in cubes:
        stack[cube.original_z_range[0]:cube.original_z_range[1],
        cube.original_y_range[0]:cube.original_y_range[1],
        cube.original_x_range[0]:cube.original_x_range[1]] = cube.totalPathLength

    max = zsu.max_project(stack)
    cv2.imwrite(config.SCANS_DIR + "\\" + stem + '_densityMap.png', max)

