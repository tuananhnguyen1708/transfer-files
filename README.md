# Transfer Files Project

Home Test for Cake Digital Banking

## Prerequisites

- Python 3.10+
- Docker
- Docker Compose

## Installation

### Setting Up Simulated SFTP Servers

1.  **Create Local Directories:**

    ```bash
    mkdir /absolute/local/path/to/source_sftp_server
    mkdir /absolute/local/path/to/target_sftp_server
    ```

    > **Note:** Replace `/absolute/local/path/to/` with the absolute path on your local machine.

2.  **Run SFTP Containers:**

    ```bash
    # Running source_sftp_server in a container, maps port 22 to port 2222 in local with user/password: sftp1/123456
    docker run --name sftp1 -p 2222:22 -v /absolute/local/path/to/source_sftp_server:/home/sftp1 -d atmoz/sftp sftp1:123456:::
    # Running target_sftp_server in a container, maps port 22 to port 2223 in local with user/password: sftp2/123456
    docker run --name sftp2 -p 2223:22 -v /absolute/local/path/to/target_sftp_server:/home/sftp2 -d atmoz/sftp sftp2:123456:::
    ```

3.  **Verify Container Status:**

    ```bash
    docker inspect -f '{{.State.Running}}' sftp1 sftp2
    # Output: 
    # true
    # true
    ```

4.  **Populate Source Directory:**

    - Create files and folders with any level of complexity in the `source_sftp_server` directory to prepare for file synchronization testing.

### Setting Up Airflow

1.  **Configure Job and Connection Settings:**

    -   **`airflow-repo/scripts/configs/source_configs.json`:** Defines connection information.

        ```json
        {
          "sftp1": {
            "type": "SFTP",
            "host": "192.168.1.3",
            "port": 2222,
            "user": "sftp1",
            "password": "123456"
          }
        }
        ```

        | Field Name | Description                                              | Example     |
        |------------|----------------------------------------------------------|-------------|
        | Object key | A unique connection name                                | sftp1       |
        | type       | Connection type                                          | SFTP, S3    |
        | host       | Connection host. If local, use the **local IP** | 192.168.1.3 |
        | port       | Connection port                                          | 2222        |
        | user       | Connection user                                          | sftp1       |
        | password   | Connection password                                      | 123456      |

        > **⚠️ Note:**
        > - In this test, connections are stored in a JSON file. In a production environment, they would be stored securely.
        > - This test only implements SFTP connections. For other connection types, the configuration structure can be extended with additional attributes (e.g., `access_key`, `key_file_path`).
        > - To run this project with the two servers above, update the `host` value with your local IP address. Use `ipconfig getifaddr en0` to get your local IP address.

    -   **`airflow-repo/scripts/configs/job_configs.json`:** Defines job configurations.

        ```json
        {
          "transfer_files_sftp1_sftp2": {
            "source_name": "sftp1",
            "source_path": "/",
            "target_name": "sftp2",
            "target_path": "/",
            "schedule_interval": "None"
          }
        }
        ```

        | Field Name        | Description                                                                 | Example                      |
        |-------------------|-----------------------------------------------------------------------------|------------------------------|
        | Object key        | A unique job name                                                          | transfer_files_sftp1_sftp2   |
        | source_name       | Source connection name (maps to connection name in source_configs.json)      | sftp1                        |
        | source_path       | Source root path for processing                                            | /, /files, /files/sub_folder |
        | target_name       | Target connection name (maps to connection name in source_configs.json)      | sftp2                        |
        | target_path       | Target root path for storing transferred files                               | /, /files, /files/sub_folder |
        | schedule_interval | DAG schedule interval                                                       | None, 0 0 * * * |

        > **⚠️ Note:**
        > - In this test, job configurations are stored in a JSON file. In a production environment, they would be stored in a database.
        > - Each object corresponds to one job and one DAG.

2.  **Generate Airflow DAGs:**

    - Run the script to generate file transfer DAGs (this step can be integrated into a CI/CD pipeline in production):

        ```bash
        python3 airflow-repo/scripts/gen_transfer_file_dags.py
        ```

    - After running, Python files are generated in the `airflow-repo/dags/sync_file` directory, named according to the job names in the configuration file.

3.  **Start Airflow with Docker Compose:**

    ```bash
    sudo docker compose -f airflow-repo/docker-compose.yaml up -d
    ```

4.  **Verify Airflow Services:**

    ```bash
    docker inspect -f '{{.State.Running}}' airflow-db-postgres airflow-redis airflow-webserver airflow-scheduler airflow-worker
    # Should output: true true true true true
    ```

5.  **Access Airflow Web UI:**

    - Open [http://localhost:8080](http://localhost:8080) and log in with the username/password: `airflow/airflow`.

## Usage

### Trigger DAGs

- Trigger the generated DAGs and verify that the target directory contains all files from the source directory.

> **⚠️ Note:**
> If there are no new files, the DAG will only run the `detect_new_files` task and skip the others.

## Assumptions

### SFTP Server

- Source and target servers are running in Docker containers.
- Firewall rules do not impede SFTP connections.
- SFTP user accounts have the necessary read/write permissions for file transfers and directory creation.
- There are no limitations regarding the depth of directories.

### File Handling

- Files to be transferred are standard files (e.g., text, data files) and do not require special handling.
- File names are unique and do not contain special characters that would cause issues during transfer.
- No file corruption will occur during transfer.

### Airflow Environment

- The latest stable version of Airflow is used as specified in `docker-compose.yml`.
- Celery executor is used for distributed task execution.
- Postgres is used for the Airflow metadata database.

### Business Requirements

- Synchronization is unidirectional from source to target.
- The original directory structure from the source is replicated on the target.
- Only new files from the source are transferred.
- "New file" is determined by the relative file path and file name (files are not compared by content).
- Files deleted on the source are not deleted on the target.

## Trade-offs

- "New file" definition (relative file path and name) can lead to inconsistencies if source file content changes.
- Listing all files on the source can be costly in a cloud environment if the source directory structure is complex.

## Solution

- To enhance scalability for future data source development, the process is divided into the following steps:

    -   **Step 1 - Detect new files on source:**
        - List all files from the source.
        - Ignore existing files on the target, processing only new files.
    -   **Step 2 - Download new files from the source to a local directory.**
    -   **Step 3 - Upload new files from the local directory to the target.**

- This approach ensures source and target server independence, using a local directory as a temporary staging area.
- An abstract class `FileTransfer` is defined with common methods (e.g., listing, downloading, uploading files).
- Each connection type has a corresponding class inheriting from `FileTransfer`.

## Q&A

#### 1. The level of abstraction in your API(s). Given that business requirements are subject to change, evaluate how adaptable your solution is if the data source transitions from SFTP to Object Storage.

- The Factory Design Pattern is used for connection type class design, allowing for easy extension and modification without changing client code.
- To implement a new connection type (e.g., S3), create a new class `S3FileTransfer` inheriting from `FileTransfer` and implement the abstract methods. Then, add a case for the `S3` type in the `init_connection()` method within `base_sync_files.py.tpl`.

#### 2. The extensibility of your API(s). Assess whether it is feasible to incorporate additional transformations before loading files into the target system without significant effort.

- The `transform()` method is available in `base_sync_files.py.tpl` and is executed before loading files to the target.
- Transformation logic should be defined clearly before implementation. If applied to all pipelines, only method logic needs updating. For conditional transformations, job configurations can be used. Direct method code updates are discouraged when transformation logic cannot be applied universally.

#### 3. Your strategy for handling anomalies. For instance, if file sizes increase dramatically from kilobytes to gigabytes, how does your solution accommodate this change in scale?

-   **Monitoring:** Track file sizes and other metrics to detect peak times when file sizes increase.
-   **Alerting:** Set up thresholds and immediate notifications for issues.
-   **Optimization:** Implement strategies for performance and large file handling:
    -   Chunking: Divide files into smaller segments for processing.
    -   Parallel Processing: Process multiple files concurrently.
    -   Optimized Data Transfer: Use efficient protocols and compression.
-   **Data Validation:** Perform post-transfer validation to ensure data integrity, especially for large files.