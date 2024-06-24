from osgeo import gdal

import enum

# import os
import numpy as np

# import psutil
# from psutil._common import bytes2human


# def memory_usage(process_id=os.getpid()):
#     process = psutil.Process(process_id)
#     # rss
#     # memory = process.memory_info()[0] / (1024**3)
#     return bytes2human(process.memory_info()[0])


def load(name: str = ""):

    if name == "":
        # TODO Environment variable, ...
        name = "lue"

    assert name in ["lue", "pcraster"]

    if name == "lue":

        import numbers
        import lue.framework as lfr
        import lue.pcraster as pcr
        import lue.pcraster.framework as pcrfw

        @lfr.runtime_scope
        def create_and_run_model(function, *args):
            function(*args)

        pcr.run_model = create_and_run_model
        pcr.partition_shape = (2000, 2000)
        pcr.partition_shape = (360, 720)

        # TODO Move to LUE(?)
        def set_clone(pathname):
            raster_dataset = gdal.Open(pathname)
            assert raster_dataset, f"Could not open {pathname}"

            array_shape = raster_dataset.RasterYSize, raster_dataset.RasterXSize

            assert pcr.partition_shape is not None, "Assign partition shape to package"
            partition_shape = pcr.partition_shape

            geo_transform = raster_dataset.GetGeoTransform()
            cell_shape = geo_transform[1], -geo_transform[5]
            assert cell_shape[0] == cell_shape[1]
            cell_size = cell_shape[0]

            pcr.configuration.array_shape = array_shape
            pcr.configuration.partition_shape = partition_shape
            pcr.configuration.cell_size = cell_size

        pcr.setclone = set_clone

        # def print_max(name, raster):
        #     print(f"{name}: {pcr.mapmaximum(raster).get()}")

        # TODO Move to LUE
        def timeinputscalar(timeseries_pathname: str, id_expression, timestep: int):
            lines = open(timeseries_pathname).readlines()
            nr_rows_to_skip = int(lines[1]) + 2
            lines = lines[nr_rows_to_skip:]
            line = lines[timestep - 1]
            values = line.split()[1:]
            lookup_table = {id_ + 1: float(values[id_]) for id_ in range(len(values))}

            if isinstance(id_expression, numbers.Number):
                return lookup_table[id_expression]
            else:
                return lfr.reclassify(id_expression, lookup_table, dtype=np.float32)

        pcr.timeinputscalar = timeinputscalar

        # TODO Move to LUE
        pcr.VALUESCALE = enum.Enum(
            "VALUESCALE",
            ["Boolean", "Directional", "Ldd", "Nominal", "Ordinal", "Scalar"],
        )
        (
            pcr.Boolean,
            pcr.Directional,
            pcr.Ldd,
            pcr.Nominal,
            pcr.Ordinal,
            pcr.Scalar,
        ) = pcr.VALUESCALE

        # TODO Move to LUE
        def numpy2pcr(data_type, array, no_data_value):
            assert (
                data_type == pcr.Ldd
                and array.dtype == np.uint8
                or data_type == pcr.Scalar
                and array.dtype == np.float32
            ), f"{data_type} vs {array.dtype}"
            return lfr.from_numpy(
                array,
                partition_shape=pcr.configuration.partition_shape,
                no_data_value=no_data_value,
            )

        pcr.numpy2pcr = numpy2pcr

        ### # TODO Move to LUE
        ### def ldd(expression):
        ###     expression = pcr.read_if_necessary(expression)[0]

        ###     if pcr.is_spatial(expression):
        ###         if pcr.is_ldd(expression):
        ###             return expression
        ###         else:
        ###             # TODO We need the casts from float to int
        ###             return lfr.cast(expression, np.uint8)
        ###     elif pcr.is_non_spatial(expression):
        ###         return np.uint8(expression)

        ###     raise RuntimeError("Unsupported argument: {}".format(expression))

        ### pcr.ldd = ldd

        # TODO Move to LUE
        def lddrepair(ldd):
            return ldd

        pcr.lddrepair = lddrepair

        # TODO Move to LUE
        def setglobaloption(option):
            print(f"discarding global option {option}\n")

        pcr.setglobaloption = setglobaloption

        # TODO Move to LUE
        def ycoordinate(expression):
            # TODO
            return (
                lfr.cast(lfr.cell_index(pcr.defined(expression), 0), np.float32)
                * pcr.configuration.cell_size
            )

        pcr.ycoordinate = ycoordinate

        # TODO Move to LUE
        def clone():

            if not hasattr(pcr.Configuration, "cellSize"):
                def cellSize(self):
                    return self.cell_size
                setattr(pcr.Configuration, "cellSize", cellSize)
            if not hasattr(pcr.Configuration, "nrRows"):
                def nrRows(self):
                    return self.array_shape[0]
                setattr(pcr.Configuration, "nrRows", nrRows)
            if not hasattr(pcr.Configuration, "nrCols"):
                def nrCols(self):
                    return self.array_shape[1]
                setattr(pcr.Configuration, "nrCols", nrCols)

            return pcr.configuration

        pcr.clone = clone

        # pcr.memory_usage = memory_usage

    elif name == "pcraster":
        # framework = pcr
        import pcraster as pcr
        import pcraster.framework as pcrfw

    return pcr, pcrfw
