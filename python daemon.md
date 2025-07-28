Running a Python script as a daemon on Ubuntu typically involves ensuring the script can run continuously in the background, independent of a user session, and often managing its lifecycle with system services.
Key considerations for a Python daemon on Ubuntu:
Daemonization:
python-daemon library: This is a recommended approach. The python-daemon library (installable via pip install python-daemon) provides a DaemonContext class that handles the complexities of becoming a well-behaved Unix daemon, including detaching from the parent process, managing file descriptors, changing directories, handling signals, and optionally managing a PID file.
Manual daemonization: While possible, it's more complex and involves steps like double-forking, closing standard file descriptors, and changing the working directory.
Service Management:
Systemd: Ubuntu uses Systemd for managing system services. Creating a Systemd service unit file (.service file) for your Python daemon allows Systemd to start, stop, restart, and monitor your script automatically, including at boot time.
Init.d scripts (older method): While still functional, Systemd is the preferred method for service management on modern Ubuntu versions.
Example using python-daemon and Systemd:
Install python-daemon.
קוד

    pip install python-daemon
Create your Python daemon script (e.g., my_daemon.py):
Python

    import os
    import time
    from daemon import DaemonContext

    def run_daemon():
        with open('/var/log/my_daemon.log', 'a') as f:
            f.write(f"Daemon started at {time.ctime()}\n")
            while True:
                f.write(f"Daemon running at {time.ctime()}\n")
                f.flush() # Ensure log is written immediately
                time.sleep(10) # Perform some task every 10 seconds

    if __name__ == '__main__':
        with DaemonContext(
            pidfile='/var/run/my_daemon.pid',
            stdout='/var/log/my_daemon.log',
            stderr='/var/log/my_daemon.log',
            working_directory='/tmp', # Choose an appropriate working directory
        ):
            run_daemon()
Create a Systemd service file (e.g., /etc/systemd/system/my_daemon.service):
קוד

    [Unit]
    Description=My Python Daemon
    After=network.target

    [Service]
    ExecStart=/usr/bin/python3 /path/to/my_daemon.py
    WorkingDirectory=/path/to/your/script/directory
    Restart=always
    User=your_username # Or a dedicated service user
    Group=your_groupname # Or a dedicated service group

    [Install]
    WantedBy=multi-user.target
Replace /path/to/my_daemon.py and /path/to/your/script/directory with the actual paths.
Adjust User and Group as needed for permissions.
Enable and start the service.
קוד

    sudo systemctl enable my_daemon.service
    sudo systemctl start my_daemon.service
This setup ensures your Python script runs as a robust daemon, managed by Systemd, providing reliability and ease of control.
