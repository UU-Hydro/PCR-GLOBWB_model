cdo timavg -selyear,1975 ../../netcdf/discharge_monthAvg_output.nc                   discharge_annuaAvg_output_1975.nc
cdo timavg -selyear,1975 ../../netcdf/gwRecharge_monthAvg_output.nc                  gwRecharge_annuaAvg_output_1975.nc
cdo timavg -selyear,1975 ../../netcdf/totalGroundwaterAbstraction_monthAvg_output.nc totalGroundwaterAbstraction_annuaAvg_output_1975.nc
pcrcalc discharge_annuaAvg_output_1975.map                   = "scalar(discharge_annuaAvg_output_1975.nc)"
pcrcalc gwRecharge_annuaAvg_output_1975.map                  = "scalar(gwRecharge_annuaAvg_output_1975.nc)"
pcrcalc totalGroundwaterAbstraction_annuaAvg_output_1975.map = "scalar(totalGroundwaterAbstraction_annuaAvg_output_1975.nc)"
