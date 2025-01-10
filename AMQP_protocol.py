# Code for latency test with AMQP protocol

import pika
import json
import random
from datetime import datetime
import csv
import time
import pytz  # For timezone-aware datetime handling
from concurrent.futures import ThreadPoolExecutor

AMQP_URL = 'Add your CloudAMQP link here' # Change to your CloudAMQP link 

# Global dictionary to store message sizes and file handles
message_sizes = {}
current_csv_file = None

def open_csv_file(interval, size):
    """Open a new CSV file for the given interval and size."""
    global current_csv_file
    file_name = f"latency_log_{int(interval*1000)}ms_{size}.csv"
    current_csv_file = open(file_name, mode='w', newline='')
    writer = csv.writer(current_csv_file)
    if current_csv_file.tell() == 0:  # Write header if the file is empty
        writer.writerow(['Sending Timestamp', 'Response Timestamp', 'Latency (ms)', 'Payload Size', 'Response'])
    return writer

def log_latency_to_csv(writer, droneID, sent_time, ack_time, latency, message_size, ack_message):
    """Log latency and message size to the current CSV file."""
    try:
        #writer.writerow([droneID, sent_time, ack_time, latency, message_size, ack_message])
        writer.writerow([sent_time, ack_time, latency, message_size, ack_message])
    except Exception as e:
        print(f"Error logging to CSV: {e}")

def on_ack(ch, method, properties, body):
    """Callback to handle acknowledgment and calculate latency."""
    ack_message = json.loads(body)
    received_time = datetime.utcnow().replace(tzinfo=pytz.utc)

    sent_time = datetime.fromisoformat(ack_message["sent_time"]).replace(tzinfo=pytz.utc)
    latency = (received_time - sent_time).total_seconds() * 1000 / 2  # in ms

    drone_id = ack_message["droneId"]
    message_size = message_sizes.get(drone_id, "Unknown")  # Get size or fallback to "Unknown"

    # Log to the appropriate CSV file
    log_latency_to_csv(csv_writer, drone_id, ack_message["sent_time"], received_time.isoformat().replace("+00:00", "Z"), latency, message_size, ack_message) 

def receive_ack():
    """Receive acknowledgments in a separate thread."""
    params = pika.URLParameters(AMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue='q_ack', durable=True, auto_delete=False, exclusive=False)
    channel.basic_consume(queue='q_ack', on_message_callback=on_ack, auto_ack=True)

    #print("Waiting for acknowledgments...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Stopping acknowledgment receiver...")
        channel.stop_consuming()
    finally:
        connection.close()

def publish_messages(intervals, sizes):
    """Publish messages for different intervals and sizes."""
    global message_sizes, csv_writer, current_csv_file

    params = pika.URLParameters(AMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue='drone_data', durable=True, auto_delete=False, exclusive=False)

    base_reason = "Violation of NFZ X. Exit the area immediately."
    for interval in intervals:
        for size in sizes:
            print(f"Testing interval: {interval}s, size: {size}.")

            # Open a new CSV file for this combination
            csv_writer = open_csv_file(interval, size)

            # Adjust `reason` field to control message size
            reason_multiplier = 1 if size == "small" else 50 if size == "medium" else 100
            reason = base_reason * reason_multiplier

            for _ in range(100):  # Send 100 messages for each configuration
                message = {
                    "droneId": f"{random.randint(100000000000, 999999999999)}",
                    "warning": "drone_detection",
                    "lon": -7.460771 + random.uniform(-0.01, 0.01),
                    "lat": 43.113822 + random.uniform(-0.01, 0.01),
                    "alt_rel": round(random.uniform(45.0, 55.0), 1),
                    "timestamp": datetime.utcnow().isoformat() + 'Z',
                    "warning_level": random.choice([1, 2]),
                    "reason": reason,
                    "token": "Dumbdronesim",
                    "sent_time": datetime.utcnow().replace(tzinfo=pytz.utc).isoformat()
                }

                message_size = len(json.dumps(message).encode('utf-8'))
                message_sizes[message["droneId"]] = message_size

                channel.basic_publish(exchange='', routing_key='drone_data', body=json.dumps(message))

                time.sleep(interval)

            # Close the CSV file after testing this configuration
            current_csv_file.close()

    print("Finished testing all intervals and sizes.")
    connection.close()

if __name__ == "__main__":
    # Define intervals (in seconds) and sizes
    intervals = [1.0, 0.5, 0.1, 0.01]  # Adjust intervals as needed
    sizes = ["small", "medium", "large"]  # Message sizes: small, medium, large

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.submit(receive_ack)  # Start receiving acknowledgments
        executor.submit(publish_messages, intervals, sizes)  # Start publishing messages
