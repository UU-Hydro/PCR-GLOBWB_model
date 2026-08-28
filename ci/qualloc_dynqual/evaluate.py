import pathlib as pl

import numpy as np
import numpy.testing as npt
import netCDF4 as nc
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf

ref_dir = pl.Path("data/reference")
out_dir = pl.Path("output")
models = ["pcrglobwb", "qualloc"]

assert ref_dir.exists(), f"Reference directory {ref_dir} does not exist."
assert out_dir.exists(), f"Output directory {out_dir} does not exist."

for model in models:
    print(f"model {model}")

    ref_model_dir = ref_dir / model
    out_model_dir = out_dir / model

    ref_netcdf_dir = ref_model_dir / "netcdf"
    out_netcdf_dir = out_model_dir / "netcdf"

    assert ref_netcdf_dir.exists(), f"Reference netcdf directory {ref_netcdf_dir} does not exist."
    assert out_netcdf_dir.exists(), f"Output netcdf directory {out_netcdf_dir} does not exist."

    ref_files = sorted(ref_netcdf_dir.glob("*.nc"))
    for ref_file in ref_files:
        print(f"ref_file: {ref_file}")

        out_file = out_netcdf_dir / ref_file.name
        assert out_file.exists(), f"Output file {out_file} does not exist."

        with nc.Dataset(ref_file) as ref_ds, nc.Dataset(out_file) as out_ds:
            ref_vars = set(ref_ds.variables.keys())
            out_vars = set(out_ds.variables.keys())
            assert ref_vars == out_vars, f"Variables in {ref_file} and {out_file} do not match."

            for var_name in ref_vars:
                if var_name in ["time", "lat", "lon"]:
                    continue  # Skip coordinate variables
                ref_var = ref_ds.variables[var_name][:]
                out_var = out_ds.variables[var_name][:]
                assert ref_var.shape == out_var.shape, f"Shape of variable {var_name} in {ref_file} and {out_file} do not match."

                rtol = 1e-2
                atol = np.max(np.abs(ref_var)) * 1e-2

                try:
                    npt.assert_allclose(ref_var, out_var, rtol=rtol, atol=atol, err_msg=f"Values of variable {var_name} in {ref_file} and {out_file} do not match.")
                except AssertionError as e:

                    diff = (ref_var - out_var)
                    rdiff = np.abs(diff / ref_var)

                    with pdf.PdfPages(out_model_dir / f"{var_name}.pdf") as pdf_pages:
                        for t in range(ref_var.shape[0]):
                            plt.subplot(2, 2, 1)
                            plt.imshow(ref_var[t, :, :], cmap="viridis", interpolation="none",)
                            plt.colorbar()
                            plt.title("reference")

                            plt.subplot(2, 2, 2)
                            plt.imshow(out_var[t, :, :], cmap="viridis", interpolation="none",)
                            plt.colorbar()
                            plt.title("output")

                            plt.subplot(2, 2, 3)
                            plt.imshow(diff[t, :, :], cmap="viridis", interpolation="none",)
                            plt.colorbar()
                            plt.title("difference")

                            plt.subplot(2, 2, 4)
                            plt.imshow(rdiff[t, :, :], cmap="viridis", vmin=0, vmax=1, interpolation="none",)
                            plt.colorbar()
                            plt.title("relative difference")

                            plt.suptitle(f"time {t}")
                            plt.tight_layout()
                            pdf_pages.savefig(dpi=300)
                            plt.close()

                    raise e
