import os
import time
import logging
import json
import pika
import uproot
import awkward as ak
import vector
import numpy as np

import os
import pika
import logging

logger = logging.getLogger(__name__)

# Environment variables for RabbitMQ
rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq-service")
rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
rabbitmq_pass = os.getenv("RABBITMQ_PASS", "guest")

def connect_to_rabbitmq():
    for attempt in range(1, 11):  # Retry up to 10 times
        try:
            credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
            parameters = pika.ConnectionParameters(
                host=rabbitmq_host,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            logger.info("Connected to RabbitMQ")
            return connection, channel
        except pika.exceptions.AMQPConnectionError:
            logger.warning(f"Attempt {attempt}: RabbitMQ not ready, retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error connecting to RabbitMQ: {e}")
            time.sleep(5)
    logger.error("Could not connect to RabbitMQ after 10 retries")
    raise Exception("Could not connect to RabbitMQ after 10 retries")

def process_mc(input_file, output_file, sample):
    logger.info(f"Processing file: {input_file}")
    try:
        if not os.path.exists(input_file):
            logger.error(f"Input file does not exist: {input_file}")
            return

        with uproot.open(f"{input_file}:mini") as tree:
            # Select variables of interest
            variables = ['lep_pt', 'lep_eta', 'lep_phi', 'lep_E', 'lep_charge', 'lep_type']
            weight_variables = ["mcWeight", "scaleFactor_PILEUP", "scaleFactor_ELE", "scaleFactor_MUON", "scaleFactor_LepTRIGGER"]
            variables += weight_variables

            # Process data in chunks
            sample_data = []
            for data in tree.iterate(variables, library="ak"):
                # Apply cuts, calculate weights, etc.
                lep_vectors = vector.zip({
                    "pt": data["lep_pt"],
                    "eta": data["lep_eta"],
                    "phi": data["lep_phi"],
                    "E": data["lep_E"],
                })

                # Example calculation: sum of first two leptons
                if ak.num(lep_vectors) >= 2:
                    mass = (lep_vectors[:, 0] + lep_vectors[:, 1]).mass
                    data['mass'] = mass
                else:
                    data['mass'] = ak.zeros_like(data['lep_pt'])

                sample_data.append(data)

            # Save processed data as parquet
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            ak.to_parquet(ak.concatenate(sample_data), output_file)
            logger.info(f"Processed data saved to {output_file}")
    except FileNotFoundError:
        logger.error(f"File not found: {input_file}")
    except Exception as e:
        logger.error(f"Error processing file {input_file}: {e}")

import json

def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        file_path = message.get("file_path")
        task = message.get("task")
        print(f"Received task: {task} for file: {file_path}")
        # Proceed with processing the file
    except json.JSONDecodeError:
        print("Failed to decode message as JSON.")

    except Exception as e:
        logger.error(f"Error in callback: {e}")

if __name__ == "__main__":
    try:
        connection, channel = connect_to_rabbitmq()
        channel.queue_declare(queue='mc_tasks')

        # Start consuming messages
        logger.info(' [*] Waiting for messages on "mc_tasks" queue. To exit press CTRL+C')
        channel.basic_consume(queue='mc_tasks', on_message_callback=callback, auto_ack=True)
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        try:
            channel.stop_consuming()
        except Exception as e:
            logger.error(f"Error stopping consumption: {e}")
        try:
            connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumer: {e}")
        exit(1)
