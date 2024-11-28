import awkward as ak
import pyarrow.parquet as pq

def flatten_array(data):
    """
    Flattens nested awkward arrays into a form compatible with Arrow tables.
    """
    # Convert awkward array to an Arrow table
    table = ak.to_arrow_table(data)
    return table

def aggregate_data(input_files, output_file):
    """
    Aggregates data from multiple Parquet files and outputs a single Parquet file.
    """
    aggregated = None
    for file in input_files:
        # Read each Parquet file into an Awkward Array
        data = ak.from_parquet(file)
        # Concatenate data
        if aggregated is None:
            aggregated = data
        else:
            aggregated = ak.concatenate([aggregated, data])
    
    # Flatten the data for compatibility with Arrow
    flattened_data = flatten_array(aggregated)
    
    # Save the flattened data as a Parquet file using pyarrow
    pq.write_table(flattened_data, output_file)

if __name__ == "__main__":
    # Define input files and output file
    input_files = [
        "output/data_A.4lep_processed.parquet",
        "output/data_B.4lep_processed.parquet",
        "output/data_C.4lep_processed.parquet",
        "output/data_D.4lep_processed.parquet"
    ]
    output_file = "output/aggregated_data.parquet"
    
    # Run the aggregation
    aggregate_data(input_files, output_file)
