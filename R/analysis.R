# --- R Script (analysis.R) ---
# This script performs statistical analysis on the input data.
# It's designed to be called from a Python script using rpy2.

# Function to perform analysis
perform_analysis <- function(data) {
  # Ensure the input is a data.frame
  if (!is.data.frame(data)) {
    stop("Input data must be a data.frame.")
  }

  # Print a message indicating that the analysis is starting
  print("Starting R analysis...")

  # Basic summary statistics
  summary_data <- summary(data)

  # Calculate correlations
  cor_matrix <- cor(data[, sapply(data, is.numeric)], use = "pairwise.complete.obs") # Only numeric cols

  # Perform a linear regression (example)
  if ("Close" %in% colnames(data) && "Volume" %in% colnames(data)) {
    tryCatch({
      lm_model <- lm(Close ~ Volume, data = data)
      lm_summary <- summary(lm_model)
    }, error = function(e) {
      print(paste("Error in linear regression: ", e))
      lm_summary <- "Linear regression failed due to data issues."
    })
  } else {
    lm_summary <- "Close or Volume columns not found. Skipping linear regression."
  }

  # Create a list to hold the results
  results <- list(
    summary = summary_data,
    correlation_matrix = cor_matrix,
    linear_model_summary = lm_summary
  )

  # Print a message indicating the analysis is complete
  print("R analysis complete.")
  return(results)
}

# Example usage (for testing within R -  comment out when calling from Python)
# data <- data.frame(
#   Date = seq(as.Date("2023-01-01"), as.Date("2023-01-10"), by = "day"),
#   Open = c(150, 152, 155, 154, 156, 158, 160, 162, 165, 164),
#   Close = c(151, 153, 156, 155, 157, 159, 161, 163, 166, 165),
#   Volume = c(1000, 1200, 1300, 1100, 1250, 1400, 1500, 1600, 1700, 1650)
# )
# results <- perform_analysis(data)
# print(results)
