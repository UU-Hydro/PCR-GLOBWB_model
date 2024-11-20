


def setclone(pathname):
    pcr.configuration.bounding_box = pcr.BoundingBox(north=90, west=-180, south=-90, east=180)
    pcr.configuration.cell_size = 0.5
    pcr.configuration.array_shape = (360, 720)
    pcr.configuration.partition_shape = (360, 720)
