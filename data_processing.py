import uproot
import awkward as ak
import vector
import numpy as np
import os
import pika
import time
import json

# Conversion factors
MeV = 0.001


# Environment variables for RabbitMQ (aligned with Kubernetes configuration)
rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq-service")
rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
rabbitmq_pass = os.getenv("RABBITMQ_PASS", "guest")

def send_rabbitmq_message(file_name):
    # Establish RabbitMQ connection
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        )
    )
    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue='mc_tasks', durable=True)

    # Create a JSON message
    message = {
        "status": "processed",
        "file_path": file_name,
        "task": "mc_simulation",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    message_body = json.dumps(message)

    # Publish the message
    channel.basic_publish(
        exchange='',
        routing_key='mc_tasks',
        body=message_body,
        properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
    )
    print(f" [x] Sent '{message_body}'")

    # Close the connection
    connection.close()
def cut_lep_type(lep_type):
    sum_lep_type = lep_type[:, 0] + lep_type[:, 1] + lep_type[:, 2] + lep_type[:, 3]
    return (sum_lep_type != 44) & (sum_lep_type != 48) & (sum_lep_type != 52)

def cut_lep_charge(lep_charge):
    return (lep_charge[:, 0] + lep_charge[:, 1] + lep_charge[:, 2] + lep_charge[:, 3]) != 0

def calc_mass(lep_pt, lep_eta, lep_phi, lep_E):
    p4 = vector.zip({"pt": lep_pt, "eta": lep_eta, "phi": lep_phi, "E": lep_E})
    return (p4[:, 0] + p4[:, 1] + p4[:, 2] + p4[:, 3]).M * MeV

def process_data(input_file, output_file):
    with uproot.open(input_file + ":mini") as tree:
        data = tree.arrays(["lep_pt", "lep_eta", "lep_phi", "lep_E", "lep_charge", "lep_type"], library="ak")

        # Apply cuts
        data = data[~cut_lep_type(data['lep_type'])]
        data = data[~cut_lep_charge(data['lep_charge'])]

        # Calculate invariant mass
        data["mass"] = calc_mass(data["lep_pt"], data["lep_eta"], data["lep_phi"], data["lep_E"])

        # Save processed data
        ak.to_parquet(data, output_file)
        print(f"Processed data saved to {output_file}")


if __name__ == "__main__":
    input_files = ["data/data_A.4lep.root", "data/data_B.4lep.root", "data/data_C.4lep.root", "data/data_D.4lep.root"]
    for input_file in input_files:
        output_file = input_file.replace(".root", "_processed.parquet").replace("data/", "output/")
        os.makedirs("output", exist_ok=True)
        
        # Process the data file
        process_data(input_file, output_file)
        
        # Notify RabbitMQ
        send_rabbitmq_message(output_file)
