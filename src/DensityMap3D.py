import config
import tifffile
import xlrd
from os import listdir
from os.path import isfile, join
from scipy.interpolate import interp1d



class Cube(object):

    def __init__(self, data, ozr, oyr, oxr, totalPathLength):
        self.data = data
        # These are tuples containing the coordinates where the cube was cut from the original scan.
        self.original_z_range = ozr
        self.original_y_range = oyr
        self.original_x_range = oxr

        self.totalPathLength = totalPathLength


def slice_into_cubes(stack, zCube, yCube, xCube):
    if (stack.shape[0] % zCube != 0) or zCube == 0:
        print("Error: slice_into_cubes(): zCube must evenly divide stack z size.")
        exit(0)
    elif (stack.shape[1] % yCube != 0) or yCube == 0:
        print("Error: slice_into_cubes(): yCube must evenly divide stack y size.")
        exit(0)
    elif (stack.shape[2] % xCube != 0) or xCube == 0:
        print("Error: slice_into_cubes(): xCube must evenly divide stack x size.")
        exit(0)

    cubes = []

    for z in range(0, stack.shape[0], zCube):
        for y in range(0, stack.shape[1], yCube):
            for x in range(0, stack.shape[2], xCube):
                zRange = (z, z + zCube)
                yRange = (y, y + yCube)
                xRange = (x, x + xCube)
                data = stack[zRange[0]:zRange[1], yRange[0]:yRange[1], xRange[0]:xRange[1]]
                tempCube = Cube(data, zRange, yRange, xRange, -1)
                cubes.append(tempCube)

    return cubes


def save_cubes_to_tif(cubes, cubesOutputDir):
    for cube in cubes:
        fileName = "cube_" + str(cube.original_z_range[0]) + "-" + str(cube.original_z_range[1])
        fileName += "_" + str(cube.original_y_range[0]) + "-" + str(cube.original_y_range[1])
        fileName += "_" + str(cube.original_x_range[0]) + "-" + str(cube.original_x_range[1]) + ".tif"
        tifffile.imwrite(cubesOutputDir + fileName, cube.data)


def parse_coords_from_filename(filename):
    coords = []
    filename = filename[5:-18]
    temp = filename.split('_')
    for item in temp:
        coord = item.split('-')
        coords.append((int(coord[0]), int(coord[1])))

    return coords


def load_aivia_excel_results_into_cubes(cube_results_dir):
    files = [f for f in listdir(cube_results_dir) if isfile(join(cube_results_dir, f))]
    cubes = []

    for file in files:

        if ".tif" in file or ".xlsx" not in file:
            print("Skipping non-excel file")
            continue

        try:
            wb = xlrd.open_workbook(cube_results_dir + file)
        except PermissionError:
            pass

        try:
            sheet = wb.sheet_by_index(4)
        except IndexError:
            coords = parse_coords_from_filename(file)
            cube = Cube(None, coords[0], coords[1], coords[2], 0)
            cubes.append(cube)
        else:

            rows = []
            rowIndex = 1
            while 1:
                name = sheet.cell_value(rowIndex, 0)
                if "Segment" in name:
                    break
                else:
                    rows.append(rowIndex)
                    rowIndex += 1

            totalPathLength = 0
            for row in rows:
                totalPathLength += sheet.cell_value(row, 1)

            coords = parse_coords_from_filename(file)
            cube = Cube(None, coords[0], coords[1], coords[2], totalPathLength)
            cubes.append(cube)

    return cubes


def map_path_lengths_to_range(cubes):
    pathLengths = []
    for cube in cubes:
        pathLengths.append(cube.totalPathLength)

    minPathLength = min(pathLengths)
    maxPathLength = max(pathLengths)
    m = interp1d([minPathLength, maxPathLength], [0, 255])
    pathLengths = m(pathLengths)

    for i in range(0, len(cubes)):
        cubes[i].totalPathLength = pathLengths[i]

    return cubes

