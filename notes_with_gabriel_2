# Principle
# - Keep proportional allocation of water withdrawn based on demand magnitude (current principle of PCR-GLOBWB 2)
# - Water allocation starts from the pixels with the best water quality

# How many loops?
# - Water quality constituents (i.e., Temp, BOD, TDS, FC, [DO, N, P])
# - Water quality thresholds for each constituent and for each sector

# Input
# - available_surface_water (without considering quality)
# - water_demand_sector (e.g., irrigation, livestock, domestic and industry) -> (industry will be splitted into manufacturing and thermoelectric)
# - water_quality_concetration_constituent [Temp, BOD, TDS, FC]
# - water_quality_thresholds
water_quality_thresholds = {
'waterTemperature': ('irrigation':1000,'domestic':1000,'thermoelectric':1000,'manufacturing':1000,'livestock':1000),    # Water temperature (oC)
'organic':          ('irrigation':15  ,'domestic':5   ,'thermoelectric':30  ,'manufacturing':30  ,'livestock':1000),    # Biochemical oxigen demand (mg/l)
'salinity':         ('irrigation':450 ,'domestic':600 ,'thermoelectric':7000,'manufacturing':7000,'livestock':100000),    # Total disolved solids (mg/l)
'pathogen':         ('irrigation':1000,'domestic':1000,'thermoelectric':1000,'manufacturing':1000,'livestock':1000),    # Fecal coliforms (cfu100/ml)
}

water_quality_dict = {'TMP':'waterTemperature','BOD':'organic','TDS':'salinity':,'FC':'pathogen'}

# Step 0
available_surface_water_with_qual = available_surface_water
for sector in ['domestic','manufacturing','livestock','thermoelectric','irrigation']:
    globals()['water_demand_remaining'+str(sector)] = water_demand_sector    # water_demand_remaining_sector
    globals()['water_demand_satisfied'+str(sector)] = 0.                     # water_demand_satisfied_sector

# Looping for every constituent
for consti in ['TMP','BOD','TDS','FC']:
    
    # Defining datasets with water quality concentrations and constituen's name
    water_quality_concetration_consti = eval(f'self.input{consti}')
    constituent = water_quality_dict[consti]
    
    # Ordering sectors from less to more stringent
    thresholds = water_quality_thresholds[constituent]
    thresholds = sorted(thresholds.items(), key=lambda item: item[1], reverse=True)
    sector_order = [threshold[0] for threshold in thresholds]
    
# Looping for every sector
    for sector in sector_order:
        
    # Defining water quality thresholds
        threshold_consti_sector = water_quality_thresholds[constituent][sector]
        
    # Defining actual water available depending on constituent threshold
        available_surface_water_with_qual_conti_sector = ifthenelse(water_quality_concetration_consti < threshold_consti_sector, available_surface_water_with_qual, 0.)
        
# Looping for every sector to keep the proportional distribution
        for sector in sector_order:
        
    # Water allocation based on proportional water demand distribution, zonation scheme and further considerations (groundwater, desalinated water)
            water_withdrawal_sector = f(current PCR-GLOBWB2 water allocation scheme using available_surface_water_with_qual_conti_sector)
    
    # Calculting remaining water available
            available_surface_water_with_qual = available_surface_water_with_qual - water_withdrawal_sector
        
    # Tracking the water demand: satisficed and remaining
            water_demand_remaining_sector = water_demand_remaining_sector - water_withdrawal_sector
            water_demand_satisficed_sector = water_demand_satisficed_sector + water_withdrawal_sector
