# Selects data for major US cities.

# Read geographical data for US cities. File US.txt taken from geonames.org:
#   http://download.geonames.org/export/dump/
cities <- read.table("US.txt", 
                     header=FALSE, 
                     sep="\t",
                     stringsAsFactors=FALSE, 
                     quote="", 
                     comment.char="")

# Select only city data with population of more than 50000.
cities <- cities[cities[, 8] == "PPL", ]
cities <- cities[cities[, 15] > 50000, ]
# and write it to a new file
write.table(cities, file="input_files/US_cities.txt", 
            quote=FALSE, sep="\t",
            row.names=FALSE, col.names=FALSE)
