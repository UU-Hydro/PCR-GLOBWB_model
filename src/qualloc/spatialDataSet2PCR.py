import os
import subprocess
import sys
import types

import pcraster as pcr

NoneType = type(None)


def cloneAttributes():
    clone = pcr.clone()
    rows, cols, cellsize = clone.nrRows(), clone.nrCols(), clone.cellSize()
    return types.SimpleNamespace(
        numberRows=rows,
        numberCols=cols,
        xResolution=cellsize,
        yResolution=cellsize,
        xLL=clone.west(),
        xUR=clone.west() + cols * cellsize,
        yLL=clone.north() - rows * cellsize,
        yUR=clone.north(),
    )


def checkCoordinate(v1, v2, delta_v1, delta_v2):
    # check coordinates using delta_v, the minimum resolution
    delta_v = min(abs(delta_v1), abs(delta_v2))
    return abs(v1 - v2) < 0.5 * delta_v


def compareSpatialAttributes(
    sourceSpatialDataSet, targetSpatialDataSet, resamplePrecision=1.0e-5
):
    """Compares the attributes of two spatial datasets defined by the spatialAttributes instance\
 taking the second input as target.\
 """
    xResampleRatio = sourceSpatialDataSet.xResolution / targetSpatialDataSet.xResolution
    yResampleRatio = sourceSpatialDataSet.yResolution / targetSpatialDataSet.yResolution
    # check whether the corner coordinates of the target area lie within the source extent
    sameCoordinates = {}
    fitsExtent = True
    for coordKey in ["xLL", "xUR", "yLL", "yUR"]:
        resolutionKey = f"{coordKey[:1]}Resolution"
        sameCoordinates[coordKey] = checkCoordinate(
            getattr(sourceSpatialDataSet, coordKey),
            getattr(targetSpatialDataSet, coordKey),
            getattr(sourceSpatialDataSet, resolutionKey),
            getattr(targetSpatialDataSet, resolutionKey),
        )
        fitsExtent &= sameCoordinates[coordKey]
    # if the corners do not match, determine whether the map fits the extent
    sameResolution = (
        abs(1 - xResampleRatio) < resamplePrecision
        and abs(1 - yResampleRatio) < resamplePrecision
    )

    # output: whether the map must be clipped or warped, and whether it must be rescaled
    return fitsExtent, sameResolution, xResampleRatio, yResampleRatio


class spatialAttributes:
    # attributes of a spatial dataset

    def __init__(self, inputFileName, maxLength=-1):
        """Returns the map attributes for the spatial file name specified"""
        # maxLength: cutoff to speed up processing of large datasets with multiple bands;
        # mapInformation holds the identifier strings and offsets of the variables of interest
        mapInformation = {}
        mapInformation["dataFormat"] = "Driver", 0, str
        mapInformation["numberRows"] = "Size is", 1, int
        mapInformation["numberCols"] = "Size is", 0, int
        mapInformation["xResolution"] = "Pixel Size =", 0, float
        mapInformation["yResolution"] = "Pixel Size =", 1, float
        mapInformation["xLL"] = "Lower Left", 0, float
        mapInformation["yLL"] = "Lower Left", 1, float
        mapInformation["xUR"] = "Upper Right", 0, float
        mapInformation["yUR"] = "Upper Right", 1, float
        mapInformation["dataType"] = "Type=", 0, str
        mapInformation["minValue"] = "Min=", 0, float
        mapInformation["maxValue"] = "Max=", 0, float
        mapInformation["noDataValue"] = "NoData Value=", 0, float
        mapAttributes = {}
        # get information with gdalinfo
        command = f'gdalinfo "{inputFileName}"'
        cOut, err = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        ).communicate()

        err = err.decode("utf-8")
        cOut = cOut.decode("utf-8")

        if len(err) > 0 and not err[:7].lower() == "warning":
            sys.exit(
                f"Error: no information could be retrieved for the spatial dataset {inputFileName}"
            )

        for mapAttribute, info in mapInformation.items():
            matched = False
            rawList = cOut.split("\n")[:maxLength]
            key = info[0]
            entryNumber = info[1]
            typeInfo = info[2]
            # iterate until the entry is found or the list is empty
            while not matched and len(rawList) > 0:
                # pop the first entry, stripping whitespace (including \r)
                entry = rawList.pop(0).strip()
                if key in entry:
                    matched = True
                    posCnt = entry.find(key)
                    if posCnt >= 0:
                        posCnt += len(key)
                        rawStr = entry[posCnt:].split(",")[entryNumber]
                        rawStr = rawStr.strip("=:() \t")
                        if typeInfo in [int, float]:
                            rawStr = rawStr.split()[0]
                        # process the raw string of the entry
                        rawStr = rawStr.strip("=:() \t")
                        if typeInfo == int:
                            try:
                                mapAttributes[mapAttribute] = int(rawStr)
                            except Exception:
                                sys.exit(
                                    f"Error: map attributes could not be processed for {mapAttribute}"
                                )
                        elif typeInfo == float:
                            try:
                                mapAttributes[mapAttribute] = float(rawStr)
                            except Exception:
                                sys.exit(
                                    f"Error: map attributes could not be processed for {mapAttribute}"
                                )
                        else:
                            mapAttributes[mapAttribute] = rawStr
            if mapAttribute in ["xResolution", "yResolution"]:
                mapAttributes[mapAttribute] = abs(mapAttributes[mapAttribute])
            if mapAttribute in mapAttributes.keys():
                setattr(self, mapAttribute, mapAttributes[mapAttribute])
            else:
                setattr(self, mapAttribute, None)


class spatialDataSet:
    """Handles the processing of spatial datasets using GDAL; \
it requires the specification of the bounding box and resolution \
stores data as numpy array in memory under the variable name specified"""

    def __init__(
        self,
        variableName,
        inputFileName,
        typeStr,
        valueScale,
        xLL,
        xUR,
        yLL,
        yUR,
        xResolution,
        yResolution,
        pixels=None,
        lines=None,
        xResampleRatio=None,
        yResampleRatio=None,
        resampleMethod="near",
        outputFileName=None,
        band=None,
        attribute=None,
        warp=False,
        test=False,
        sqlStr="",
        compareStr="=",
        burnValue=None,
    ):

        tempFileRoot = f"temp_{variableName}"
        if isinstance(outputFileName, NoneType):
            outputFileName = f"{tempFileRoot}.map"
        if len(sqlStr) > 0 and not isinstance(burnValue, types.NoneType):
            sqlStr = f"-where \"{attribute}{compareStr}'{sqlStr}'\""
            sqlStr += f" -burn {burnValue:f}"
        else:
            sqlStr = ""
        if not isinstance(valueScale, str):
            try:
                valueScale = str(valueScale)
            except Exception:
                valueScale = "SCALAR"
            valueScale = valueScale.upper()

        # handle special cases such as shape files and bands
        if os.path.splitext(inputFileName)[1] == ".shp":
            command = (
                f"gdal_rasterize -a {attribute} {sqlStr} -ot {typeStr}"
                f" -tr {xResolution:f} {yResolution:f} -te {xLL:f} {yLL:f} {xUR:f} {yUR:f}"
                f'  "{inputFileName}" "{tempFileRoot}.tif" -q'
            )
            if test:
                print(command)
            cOut, err = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            ).communicate()

            err = err.decode("utf-8")
            cOut = cOut.decode("utf-8")

            if err != "" and not err[:7].lower() == "warning":
                sys.exit(
                    f"Error: no information could be retrieved from the spatial dataset {inputFileName}"
                )
            inputFileName = f"{tempFileRoot}.tif"
        elif band != 0 and not isinstance(band, NoneType):
            command = (
                f"gdal_translate -ot {typeStr} -of PCRaster -b {band} -mo VALUESCALE=VS_{valueScale}"
                f' "{inputFileName}" "{tempFileRoot}_{band}.map" -q'
            )
            if test:
                print(command)
            cOut, err = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            ).communicate()

            if (
                err != ""
                and b"warning" not in err.lower()
                and not os.path.isfile(f"{tempFileRoot}_{band}.map")
            ):
                sys.exit(
                    f"Error: no information could be retrieved from the spatial dataset {inputFileName}"
                )
            inputFileName = f"{tempFileRoot}_{band}.map"

        if warp:
            # warp the dataset and reset the resolution
            command = (
                f"gdalwarp -of GTiff -ot {typeStr} -te {xLL:f} {yLL:f} {xUR:f} {yUR:f}"
                f" -tr {xResolution:f} {yResolution:f} -r {resampleMethod}"
                f' "{inputFileName}" "{tempFileRoot}2.tif" -q -overwrite -nomd'
            )
            if test:
                print(command)
            cOut, err = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            ).communicate()
            if err != "" and not err[:7].lower() == "warning":
                sys.exit(
                    f"Error: no information could be retrieved from the spatial dataset {inputFileName}"
                )
            inputFileName = f"{tempFileRoot}2.tif"
            xResampleRatio = 1.0
            yResampleRatio = 1.0

        # convert to a PCRaster map of the chosen extent
        if not isinstance(pixels, NoneType) and not isinstance(lines, NoneType):
            command = (
                f"gdal_translate -ot {typeStr} -of PCRaster -mo VALUESCALE=VS_{valueScale}"
                f" -projwin {xLL:f} {yUR:f} {xUR:f} {yLL:f} -outsize {int(pixels)} {int(lines)}"
                f' "{inputFileName}" "{outputFileName}" -q'
            )
        elif not isinstance(xResampleRatio, NoneType) and not isinstance(
            xResampleRatio, NoneType
        ):
            command = (
                f"gdal_translate -ot {typeStr} -of PCRaster -mo VALUESCALE=VS_{valueScale}"
                f" -projwin {xLL:f} {yUR:f} {xUR:f} {yLL:f}"
                f" -outsize {100.0 * xResampleRatio:.3f}% {100.0 * yResampleRatio:.3f}%"
                f' "{inputFileName}" "{outputFileName}" -q'
            )
        else:
            sys.exit(
                "Error: no information on resample ratio / output extent is specified"
            )
        if test:
            print(command)
        cOut, err = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        ).communicate()

        if len(err) > 0 and b"warning" not in err.lower():
            sys.exit(
                f"Error: no information could be retrieved from the spatial dataset {inputFileName}"
            )
        setattr(self, variableName, pcr.readmap(outputFileName))
        for tempFileName in os.listdir(os.getcwd()):
            if os.path.splitext(tempFileName)[1] in [".map", ".tif", ".xml"]:
                if tempFileRoot in tempFileName:
                    try:
                        os.remove(tempFileName)
                    except Exception:
                        pass
