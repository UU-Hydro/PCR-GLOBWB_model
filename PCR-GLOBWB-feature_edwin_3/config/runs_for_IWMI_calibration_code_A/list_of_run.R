# make list for new runs on 22 November 2014

min_soil_depth_frac = seq( 0.5,1.5,0.5)
log_ksat            = 0	
log_recession_coef  = seq(-1.0,1.0,0.5)	
degree_day_factor   = seq( 0.5,1.5,0.5)

general_output_folder_name = 'code__a__'
start_folder_index  = 1 

# file name for the output table that will contain new parameters
new_parameter_table_file_name = "new_table_22_nov_2014.txt"

# list of existing parameters sets that have been defined in the previous runs
existing_parameters = NULL
existing_parameters = cbind(1.0, 0.0, 0.0, 1.0) # reference run         # TODO: read this one from an existing file              

# output: list of new model parameters and their folders
parameters_for_these_runs = NULL

index_folder = start_folder_index - 1
for (im in seq (along = min_soil_depth_frac)) {
for (ik in seq (along = log_ksat           )) {
for (ir in seq (along = log_recession_coef )) {
for (id in seq (along = degree_day_factor  )) {

parameters = c(min_soil_depth_frac[im], log_ksat[ik], log_recession_coef[ir], degree_day_factor[id]) 

# check if parameters already defined in the previous run
if (tail(duplicated(rbind(existing_parameters, parameters)),1)) {

print(paste("The parameter set :",parameters[1],
                                  parameters[2],
                                  parameters[3],
                                  parameters[4],
                                 " have been defined/used in previous runs.", sep = " "))

} else {

print(paste("New parameter set :",parameters[1],
                                  parameters[2],
                                  parameters[3],
                                  parameters[4],
                                 ".", sep = " "))

# updating existing parameter table
existing_parameters = rbind(existing_parameters, parameters)

# updating new parameter table
index_folder = index_folder + 1
folder_name = paste(general_output_folder_name,as.character(index_folder),sep="")
new_run = c(folder_name, parameters)
parameters_for_these_runs = rbind(parameters_for_these_runs, new_run)

} # end for if (tail(duplicated(rbind(existing_parameters, parameters)),1)) 

}
}
}
}

# assign names and write new parameters to a file
parameters_for_these_runs = data.frame(parameters_for_these_runs)
names(parameters_for_these_runs)[1] <- "output_folder"
names(parameters_for_these_runs)[2] <- "min_soil_depth_frac"
names(parameters_for_these_runs)[3] <- "log_ksat"
names(parameters_for_these_runs)[4] <- "log_recession_coef"
names(parameters_for_these_runs)[5] <- "degree_day_factor"
write.table(parameters_for_these_runs, new_parameter_table_file_name, row.names=FALSE, col.names=TRUE,sep=" ", quote=FALSE)

test = read.table("new_table_22_nov_2014.txt",header=T)
print(test)
