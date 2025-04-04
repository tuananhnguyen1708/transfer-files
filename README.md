# trans-files-project

Cake Digital Banking's home test

## Prerequisites
- Python 3.9+
- Docker

## Installation
- Build Aiflow from docker-compose.yaml
- Set up simulated source and destination SFTP servers: source_sftp_server, dest_sftp_server
```bash
# Create source_sftp_server folder to mount with source sftp server 
mkdir source_sftp_server
# Create dest_sftp_server folder to mount with destination sftp server
mkdir dest_sftp_server

# Running source_sftp_server in a container, maps port 22 to port 2222 in local with user/password: sftp1/123456
docker run -p 2222:22 -v /local/absolute/path/to/source_sftp_server:/home/sftp1 -d atmoz/sftp sftp1:123456:::
# Running dest_sftp_server in a container, maps port 22 to port 2223 in local with user/password: sftp2/123456
docker run -p 2223:22 -v /local/absolute/path/to/dest_sftp_server:/home/sftp2 -d atmoz/sftp sftp2:123456:::
```

## Usage