# trans-files-project

Cake Digital Banking's home test

## Prerequisites
- Python 3.10+
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

## Usage
### Build DAGs by scripts
- There are 2 config files which describe job information (in this test, using json files such as a database):

`airflow-repo/scripts/configs/source_configs.json`: This file includes the information of all connections.
```json
{
  "sftp1": { // an unique connection name
    "type": "SFTP",  // connection type: SFTP,S3,etc
    "host": "192.168.1.3", // connection host. If host is local, fill the local IP   
    "port": 2222, // connection port
    "user": "sftp1", // connection user
    "password": "123456" // connection password
  }
}
```

`airflow-repo/scripts/configs/job_configs.json`:
```json
{
  "transfer_files_sftp1_sftp2": { // an unique job name which is used as DAG id
    "source_name": "sftp1",  // source connection name which maps to connection name in source_configs.json
    "source_path": "/", // source root path which folder needs to processed 
    "target_name": "sftp2", // target connection name which maps to connection name in source_configs.json
    "target_path": "/" // target root path which folder saved all files after transfering
  }
}
```
- Update config 2 files to set up 1 or many transfer files DAGs.
- Run scripts to build all transfer files DAGs (This step can be set up in CI pipeline in production):
```bash
python3 airflow-repo/scripts/gen_transfer_file_dags.py
```
- After running, all python files are generated in `airflow-repo/dags/sync_file` folder with name such as job name in config file. Also, all DAGs will appear in Airflow UI.  

### Trigger DAG
- Trigger generated DAGs and verify that the target folder contains all files from the source folder.