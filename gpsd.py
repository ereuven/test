import subprocess
import time
import os
import glob
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GPSD_PROCESS = None
DETECTED_DEVICE = None

def start_gpsd(device_path):
    """Starts the gpsd daemon for the given device."""
    global GPSD_PROCESS
    logging.info(f"Starting gpsd for {device_path}...")
    try:
        # -N: Don't daemonize, -D 3: Debug level 3 for verbose output, -F: Control socket
        GPSD_PROCESS = subprocess.Popen(['gpsd', '-N', '-D', '3', device_path, '-F', '/var/run/gpsd.sock'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logging.info(f"gpsd started with PID: {GPSD_PROCESS.pid}")
        # Log initial output from gpsd to ensure it's starting
        time.sleep(1) # Give gpsd a moment to start and produce output
        if GPSD_PROCESS.poll() is None: # Check if process is still running
            logging.info("Initial gpsd output (if any):")
            for _ in range(5): # Read a few lines
                line = GPSD_PROCESS.stdout.readline().strip()
                if line:
                    logging.info(f"  GPSD_OUT: {line}")
                else:
                    break
        else:
            logging.error(f"gpsd failed to start for {device_path}. Exit code: {GPSD_PROCESS.returncode}")
            stdout, stderr = GPSD_PROCESS.communicate()
            logging.error(f"gpsd stdout: {stdout}")
            logging.error(f"gpsd stderr: {stderr}")
            GPSD_PROCESS = None
            return False
        return True
    except FileNotFoundError:
        logging.error("gpsd command not found. Ensure gpsd is installed and in your PATH.")
        return False
    except Exception as e:
        logging.error(f"Error starting gpsd: {e}")
        return False

def stop_gpsd():
    """Stops the currently running gpsd daemon."""
    global GPSD_PROCESS
    if GPSD_PROCESS and GPSD_PROCESS.poll() is None:
        logging.info("Stopping gpsd...")
        GPSD_PROCESS.terminate()
        GPSD_PROCESS.wait(timeout=5)
        if GPSD_PROCESS.poll() is None:
            logging.warning("gpsd did not terminate gracefully, killing process.")
            GPSD_PROCESS.kill()
        logging.info("gpsd stopped.")
        GPSD_PROCESS = None

def find_ttyusb_device():
    """Finds the first available /dev/ttyUSB* device."""
    ttyusb_devices = glob.glob('/dev/ttyUSB*')
    if ttyusb_devices:
        return sorted(ttyusb_devices)[0] # Return the first one found
    return None

def main():
    global DETECTED_DEVICE

    while True:
        current_device = find_ttyusb_device()

        if current_device and current_device != DETECTED_DEVICE:
            logging.info(f"New /dev/ttyUSB device detected: {current_device}")
            stop_gpsd() # Stop any existing gpsd instance
            DETECTED_DEVICE = current_device
            start_gpsd(DETECTED_DEVICE)
        elif not current_device and DETECTED_DEVICE:
            logging.warning(f"Device {DETECTED_DEVICE} disconnected.")
            stop_gpsd()
            DETECTED_DEVICE = None
        elif current_device and current_device == DETECTED_DEVICE:
            # Device still connected, check if gpsd is still running
            if GPSD_PROCESS and GPSD_PROCESS.poll() is not None:
                logging.warning(f"gpsd process for {DETECTED_DEVICE} unexpectedly terminated. Restarting...")
                stop_gpsd()
                start_gpsd(DETECTED_DEVICE)
            elif not GPSD_PROCESS:
                logging.info(f"Device {DETECTED_DEVICE} is present but gpsd is not running. Starting gpsd.")
                start_gpsd(DETECTED_DEVICE)

        time.sleep(5) # Check every 5 seconds

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Script interrupted by user. Exiting.")
        stop_gpsd()
