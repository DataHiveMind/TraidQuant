# --- Python Code (backtest.py) ---
# Initial data loading, preprocessing, and orchestration
# Key focus: Data manipulation, feature engineering, and overall backtest control
import pandas as pd
import numpy as np
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
import matlab.engine
import subprocess
import os
import time

def load_data(file_path, file_type="csv"):
    """
    Loads data from a CSV or Parquet file into a Pandas DataFrame.

    Args:
        file_path (str): Path to the data file.
        file_type (str, optional): Type of file ("csv" or "parquet"). Defaults to "csv".

    Returns:
        pd.DataFrame: The loaded data.  Returns None on error, prints error.
    """
    try:
        if file_type == "csv":
            return pd.read_csv(file_path)
        elif file_type == "parquet":
            return pd.read_parquet(file_path)
        else:
            print(f"Error: Unsupported file type: {file_type}")
            return None
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def preprocess_data(df):
    """
    Preprocesses the data, handling missing values and performing initial feature engineering.
    This is a placeholder;  Add more sophisticated techniques as needed.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: Preprocessed DataFrame. Returns None on error, prints error.
    """
    if df is None:
        return None
    try:
        # Basic example: Fill missing values with the mean
        df_filled = df.fillna(df.mean())
        # Simple feature engineering example: Calculate a moving average
        df_filled['MA_5'] = df_filled['Close'].rolling(window=5).mean()
        return df_filled
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        return None

def run_r_analysis(df, r_script_path="analysis.R"):
    """
    Runs an R script for statistical analysis using rpy2.

    Args:
        df (pd.DataFrame): Input DataFrame to be passed to R.
        r_script_path (str): Path to the R script.  Defaults to "analysis.R".

    Returns:
        dict or None: Results from the R script.  Returns None on error.  R's lists are converted to Python dictionaries.
    """
    if df is None:
        return None
    try:
        # Initialize R environment
        robjects.r['source'](r_script_path)  # Load the R script
        r_function = robjects.globalenv['perform_analysis']  # Get the R function
        pandas2ri.activate()  # Enable Pandas to R conversion
        r_df = pandas2ri.py2rpy(df)  # Convert Pandas DataFrame to R DataFrame
        r_result = r_function(r_df)  # Call the R function with the DataFrame
        # Convert the R result to a Python dictionary.  Handles nested lists.
        result_dict = dict()
        for name, value in r_result.items():
            if isinstance(value, robjects.vectors.ListVector):
                result_dict[name] = {k:v for k,v in value.items()}
            else:
                result_dict[name] = value
        return result_dict
    except Exception as e:
        print(f"Error running R analysis: {e}")
        return None

def run_matlab_simulation(df, matlab_script_path="simulation.m"):
    """
    Runs a MATLAB simulation script.  Requires a running MATLAB engine.

    Args:
        df (pd.DataFrame): Input DataFrame to be passed to MATLAB.  Converted to a struct.
        matlab_script_path (str): Path to the MATLAB script. Defaults to "simulation.m".

    Returns:
        dict or None: Results from the MATLAB simulation, or None on error.
    """
    if df is None:
        return None
    try:
        eng = matlab.engine.start_matlab()
        # Convert Pandas DataFrame to a dictionary (MATLAB struct equivalent)
        data_dict = df.to_dict(orient='list')

        # Ensure all lists are of the same length, padding with NaNs if necessary
        max_len = max(len(v) for v in data_dict.values())
        for key, value in data_dict.items():
            if len(value) < max_len:
                data_dict[key] += [np.nan] * (max_len - len(value))

        # Convert the dictionary to a MATLAB struct
        try:
            matlab_data = eng.struct(data_dict)
        except Exception as e:
            print(f"Error converting data to MATLAB struct: {e}")
            eng.quit()
            return None

        # Call the MATLAB function.
        result = eng.eval(f"run('{matlab_script_path}')", nargout=1) # Capture output

        eng.quit()
        return result # Return the result.
    except Exception as e:
        print(f"Error running MATLAB simulation: {e}")
        return None

def run_backtest(df):
    """
    Executes a simple backtesting strategy.  This is a placeholder.

    Args:
        df (pd.DataFrame): DataFrame with data, including potential features.

    Returns:
        dict or None: Backtesting results (e.g., returns, metrics), or None on error.
    """
    if df is None:
        return None
    try:
        # Example strategy: Buy if MA_5 > Close, sell if MA_5 < Close
        df['Position'] = np.where(df['MA_5'] > df['Close'], 1, -1)
        df['Lagged_Position'] = df['Position'].shift(1)
        df['Returns'] = df['Close'].pct_change()
        df['Strategy_Returns'] = df['Lagged_Position'] * df['Returns']
        cumulative_returns = (df['Strategy_Returns'] + 1).cumprod() - 1
        # Basic metrics
        total_return = cumulative_returns.iloc[-1]
        average_annual_return = (total_return + 1)**(252/len(df)) - 1 # Crude estimate
        # Volatility is often annualized
        annualized_volatility = df['Strategy_Returns'].std() * np.sqrt(252)
        sharpe_ratio = average_annual_return / annualized_volatility if annualized_volatility > 0 else 0

        results = {
            'cumulative_returns': cumulative_returns.tolist(),
            'total_return': total_return,
            'average_annual_return': average_annual_return,
            'annualized_volatility': annualized_volatility,
            'sharpe_ratio': sharpe_ratio
        }
        return results
    except Exception as e:
        print(f"Error in backtesting: {e}")
        return None

def main(data_file="data.csv", r_script="analysis.R", matlab_script="simulation.m", file_type="csv"):
    """
    Main function to orchestrate the backtesting process.

    Args:
        data_file (str): Path to the data file. Defaults to "data.csv".
        r_script (str): Path to the R script. Defaults to "analysis.R".
        matlab_script (str): Path to the MATLAB script. Defaults to "simulation.m".
        file_type (str): Type of file ("csv" or "parquet"). Defaults to "csv".
    """
    print("Starting backtesting process...")
    start_time = time.time()

    # 1. Load Data (Python)
    print(f"Loading data from {data_file}...")
    df = load_data(data_file, file_type)
    if df is None:
        print("Failed to load data. Exiting.")
        return

    # 2. Preprocess Data (Python)
    print("Preprocessing data...")
    df_processed = preprocess_data(df)
    if df_processed is None:
        print("Failed to preprocess data. Exiting.")
        return

    # 3. Run R Analysis
    print("Running R analysis...")
    r_results = run_r_analysis(df_processed, r_script)
    if r_results is None:
        print("Failed to run R analysis. Continuing (with potential issues).")
        r_results = {} # Ensure it is defined

    # 4. Run MATLAB Simulation
    print("Running MATLAB simulation...")
    matlab_results = run_matlab_simulation(df_processed, matlab_script)
    if matlab_results is None:
        print("Failed to run MATLAB simulation. Continuing (with potential issues).")
        matlab_results = {} # Ensure it is defined

    # 5. Run Backtest (Python)
    print("Running backtest in Python...")
    backtest_results = run_backtest(df_processed)
    if backtest_results is None:
        print("Failed to run backtest. Exiting.")
        return

    # 6. Combine and Print Results (Python)
    print("Combining and printing results...")
    combined_results = {
        'r_results': r_results,
        'matlab_results': matlab_results,
        'backtest_results': backtest_results
    }

    print("--- Backtesting Results ---")
    print(f"Total Return: {backtest_results.get('total_return', 'N/A'):.4f}")
    print(f"Annualized Return: {backtest_results.get('average_annual_return', 'N/A'):.4f}")
    print(f"Annualized Volatility: {backtest_results.get('annualized_volatility', 'N/A'):.4f}")
    print(f"Sharpe Ratio: {backtest_results.get('sharpe_ratio', 'N/A'):.4f}")

    print("\n--- R Analysis Results ---")
    print(r_results) # Print the whole R result dictionary

    print("\n--- MATLAB Simulation Results ---")
    print(matlab_results) # Print the whole MATLAB result.

    end_time = time.time()
    print(f"Backtesting process completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    # You can modify the file paths and script names here.
    # For Parquet, change data_file and set file_type="parquet"
    main(data_file="data.csv", r_script="analysis.R", matlab_script="simulation.m", file_type="csv")
    # main(data_file="data.parquet", r_script="analysis.R", matlab_script="simulation.m", file_type="parquet")
