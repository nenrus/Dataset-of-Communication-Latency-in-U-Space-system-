# Code for latency test with REST-API protocol

import requests
import time
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import PriorityQueue
import random

# Define the URL
url = 'Add your destination link here' # Change to your destination link server

# Define different payload sizes
payloads = {
    'small': {
        "droneId": f"{random.randint(100000000000, 999999999999)}",  # Random 12-digit ID
        "warning": "drone_detection",
        "lon": -7.460771 + random.uniform(-0.01, 0.01),  # Slightly vary longitude
        "lat": 43.113822 + random.uniform(-0.01, 0.01),  # Slightly vary latitude
        "alt_rel": round(random.uniform(45.0, 55.0), 1),  # Random altitude between 45.0 and 55.0
        "timestamp": datetime.utcnow().isoformat() + 'Z',  # Random time within the last minute
        "warning_level": random.choice([1, 2]),  # Random warning level from 1 or 2
        "reason": "Violation of NFZ X. Exit the area immediately.",
        "token": "Dumbdronesim"
        },
    'medium': {
        "droneId": f"{random.randint(100000000000, 999999999999)}",  # Random 12-digit ID
        "warning": "drone_detection",
        "lon": -7.460771 + random.uniform(-0.01, 0.01),  # Slightly vary longitude
        "lat": 43.113822 + random.uniform(-0.01, 0.01),  # Slightly vary latitude
        "alt_rel": round(random.uniform(45.0, 55.0), 1),  # Random altitude between 45.0 and 55.0
        "timestamp": datetime.utcnow().isoformat() + 'Z',  # Random time within the last minute
        "warning_level": random.choice([1, 2]),  # Random warning level from 1 or 2
        "reason": "Violation of NFZ X. Exit the area immediately." *10 ,
        "token": "Dumbdronesim"
        },
    'large': {
        "droneId": f"{random.randint(100000000000, 999999999999)}",  # Random 12-digit ID
        "warning": "drone_detection",
        "lon": -7.460771 + random.uniform(-0.01, 0.01),  # Slightly vary longitude
        "lat": 43.113822 + random.uniform(-0.01, 0.01),  # Slightly vary latitude
        "alt_rel": round(random.uniform(45.0, 55.0), 1),  # Random altitude between 45.0 and 55.0
        "timestamp": datetime.utcnow().isoformat() + 'Z',  # Random time within the last minute
        "warning_level": random.choice([1, 2]),  # Random warning level from 1 or 2
        "reason": "Violation of NFZ X. Exit the area immediately." *100 ,
        "token": "Dumbdronesim"        
        }
}

# Function to send a single request
def send_request(index, payload_size, delay):
    # Get the current timestamp in the precise format
    sending_timestamp = datetime.utcnow().isoformat(timespec='microseconds') + 'Z'

    try:
        # Send the POST request with a timeout
        response = requests.post(url, json=payloads[payload_size], timeout=5)
        #print("response: ", response)
        # Extract the response time
        #response_timestamp = response.json()['utm_ts']
        response_timestamp = datetime.utcnow().isoformat(timespec='microseconds') + 'Z'
        
        # Get status code and response text
        status_code = response.status_code
        response_text = response.text

    except requests.exceptions.RequestException as e:
        # Handle cases where the server does not respond or an error occurs
        response_timestamp = datetime.utcnow().isoformat(timespec='microseconds') + 'Z'
        status_code = 'N/A'  # No status code available
        response_text = str(e)  # Log the exception as the response text
    
    # Calculate latency in milliseconds
    sending_time = datetime.strptime(sending_timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
    response_time = datetime.strptime(response_timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
    latency = (response_time - sending_time).total_seconds() * 1000 / 2  # Convert to milliseconds (round time/2)

    # Return the index and the relevant data for logging
    return index, sending_timestamp, response_timestamp, latency, status_code, response_text

# Function to run tests for different delays and payload sizes
def run_tests():
    # Define the delays and payload sizes to test
    delays = [1.0, 0.5, 0.1, 0.01]  # 1000 ms, 500 ms, 100 ms, 10 ms
    payload_sizes = ['small', 'medium', 'large']

    # Open a CSV file to log the throughput data
    throughput_log_filename = 'throughput_log.csv'
    with open(throughput_log_filename, mode='w', newline='') as throughput_file:
        throughput_writer = csv.writer(throughput_file)
        throughput_writer.writerow(['Delay (ms)', 'Payload Size', 'Total Time (s)', 'Throughput (requests/second)'])

        for delay in delays:
            for payload_size in payload_sizes:
                log_filename = f'log_{int(delay*1000)}ms_{payload_size}.csv'
                
                # Open a CSV file to log the messages and responses
                with open(log_filename, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Sending Timestamp', 'Response Timestamp', 'Latency (ms)', 'Payload Size', 'Status Code', 'Response'])

                    # Use a ThreadPoolExecutor to send and receive messages concurrently
                    with ThreadPoolExecutor(max_workers=10) as executor:
                        futures = []
                        log_queue = PriorityQueue()
                        next_log_index = 0

                        # Submit 100 tasks to the executor with the specified interval between each send
                        start_time = time.time()
                        for index in range(100):
                            future = executor.submit(send_request, index, payload_size, delay)
                            futures.append(future)
                            #print("interval: ", delay)
                            time.sleep(delay)  # Ensure the specified delay between each send

                        # Calculate throughput
                        end_time = time.time()
                        total_time = end_time - start_time
                        throughput = 100 / total_time

                        # Process each completed future as it finishes
                        for future in as_completed(futures):
                            result = future.result()
                            log_queue.put(result)

                            # Write log entries in order of their original sending index
                            while not log_queue.empty() and log_queue.queue[0][0] == next_log_index:
                                index, sending_timestamp, response_timestamp, latency, status_code, response_text = log_queue.get()
                                writer.writerow([sending_timestamp, response_timestamp, latency, payload_size, status_code, response_text])
                                next_log_index += 1

                # Log throughput data after each test
                throughput_writer.writerow([int(delay * 1000), payload_size, total_time, throughput])

                print(f"Finished testing with {int(delay*1000)} ms delay and {payload_size} payload size.")
                print(f"Throughput: {throughput:.2f} requests/second")
                print("Messages sent, latencies calculated, and logged successfully.")

# Run the tests
run_tests()
