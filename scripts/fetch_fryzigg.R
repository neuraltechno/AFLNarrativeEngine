# Load necessary library
library(fitzRoy)
library(readr)

# Fetch data
print("Fetching Fryzigg player stats for 2026...")
data <- fitzRoy::fetch_player_stats_fryzigg(2026)

# Save to CSV
output_path <- "data/raw/fryzigg_player_stats_2026.csv"
write_csv(data, output_path)
print(paste("Data saved to", output_path))
