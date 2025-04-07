# trans-files-project

Cake Digital Banking's home test

## Prerequisites
- Python 3.9+
- Docker

## Installation
### SFTP Server
- Set up simulated source and target SFTP servers: `source_sftp_server`, `target_sftp_server`.
```bash
# Create source_sftp_server folder to mount with source sftp server 
mkdir /absolute/local/path/to/source_sftp_server
# Create target_sftp_server folder to mount with target sftp server
mkdir /absolute/local/path/to/target_sftp_server

# Running source_sftp_server in a container, maps port 22 to port 2222 in local with user/password: sftp1/123456
docker run --name sftp1 -p 2222:22 -v /absolute/local/path/to/source_sftp_server:/home/sftp1 -d atmoz/sftp sftp1:123456:::
# Running target_sftp_server in a container, maps port 22 to port 2223 in local with user/password: sftp2/123456
docker run --name sftp2 -p 2223:22 -v /absolute/local/path/to/target_sftp_server:/home/sftp2 -d atmoz/sftp sftp2:123456:::
```
- Checking if 2 containers are running:
```bash
docker inspect -f '{{.State.Running}}' sftp1 sftp2
# true
# true
```
- After 2 servers are running, let's create some files/folders with any level of complexity in folder `source_sftp_server` to prepare for sync files testing.

### Airflow
- Update `source_host` value and `target_host` value in `config` variable in `sync_files.py` by local IP.
- Build Aiflow from `docker-compose.yaml`:
```bash
sudo docker compose -f airflow-repo/docker-compose.yaml up
```
- Checking if all Airflow services are running:
```bash
docker inspect -f '{{.State.Running}}' sftp1 sftp2
# true
# true
# true
# true
# true
```
- Access to http://localhost:8080 and login by user/password: `airflow/airflow`.
- Checking if `sync_files` DAG is available.

## Usage
- Trigger the `sync_files` DAG and verify that the `target_sftp_server` folder contains all files from the `source_sftp_server` folder.