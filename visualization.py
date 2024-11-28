import awkward as ak
import numpy as np
import matplotlib.pyplot as plt

def plot_histogram(data_file, output_plot):
    data = ak.from_parquet(data_file)
    bin_edges = np.linspace(80, 250, 50)
    hist, bins = np.histogram(ak.to_numpy(data["mass"]), bins=bin_edges)
    
    plt.figure(figsize=(8, 6))
    plt.hist(bins[:-1], bins, weights=hist, alpha=0.7, label="Data")
    plt.xlabel("4-lepton invariant mass [GeV]")
    plt.ylabel("Events")
    plt.title("H → ZZ → 4l Analysis")
    plt.legend()
    plt.savefig(output_plot)
    print(f"Histogram saved to {output_plot}")

if __name__ == "__main__":
    plot_histogram("output/aggregated_data.parquet", "output/histogram.png")
