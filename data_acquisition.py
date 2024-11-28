import os
import requests

# ATLAS Open Data directory
base_url = "https://atlas-opendata.web.cern.ch/atlas-opendata/samples/2020/4lep/"
data_samples = ['data_A', 'data_B', 'data_C', 'data_D']
mc_samples = [
    "mc_361106.Zee.4lep.root",
    "mc_361107.Zmumu.4lep.root",
    "mc_361108.Ztautau.4lep.root",
    "mc_410000.ttbar_lep.4lep.root",
    "mc_410155.ttW.4lep.root",
]

def download_files(samples, subdir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for sample in samples:
        file_name = f"{sample}" if subdir == "MC" else f"{sample}.4lep.root"
        file_path = os.path.join(output_dir, file_name)
        if not os.path.exists(file_path):
            print(f"Downloading {file_name}...")
            url = f"{base_url}{subdir}/{file_name}" if subdir else f"{base_url}{file_name}"
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Downloaded: {file_path}")
            else:
                print(f"Failed to download {file_name}. Error: {response.status_code}")
        else:
            print(f"File already exists: {file_path}")

if __name__ == "__main__":
    print("Downloading data samples...")
    download_files(data_samples, "Data", "data")
    print("\nDownloading MC samples...")
    download_files(mc_samples, "MC", "data/MC")
