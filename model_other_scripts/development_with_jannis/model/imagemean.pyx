cimport cython
from libc.math cimport isnan, NAN

@cython.boundscheck(False)
def downsample(double[:, :] input, double[:, :] output):
    cdef Py_ssize_t i, j, k, l
    cdef double total, x
    cdef unsigned non_nan
    cdef unsigned ratio = input.shape[0] // output.shape[0]

    for i in range(output.shape[0]):
        for j in range(output.shape[1]):
            non_nan = 0
            total = 0.
            for k in range(ratio):
                for l in range(ratio):
                    x = input[i * ratio + k, j * ratio + l]
                    if not isnan(x):
                        total += x
                        non_nan += 1
            if non_nan != 0:
                output[i, j] = total / non_nan
            else:
                output[i, j] = NAN
