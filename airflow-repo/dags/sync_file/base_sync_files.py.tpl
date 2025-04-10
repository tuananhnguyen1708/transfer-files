from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.utils.context import Context
from airflow.exceptions import AirflowSkipException
from sync_file.file_transfer_module.file_transfer import FileTransfer
from sync_file.file_transfer_module.sftp_file_transfer import SFTPFileTransfer

config = {{ config }}


def init_connection(conn_config: dict) -> FileTransfer:
    match conn_config['type']:
        case 'SFTP':
            return SFTPFileTransfer(host=conn_config['host'], port=conn_config['port'], username=conn_config['user'],
                                    password=conn_config['password'], root_path=conn_config['path'])
        case _:
            msg = f"Connection type {type} isn't supported"
            raise Exception(msg)


def init_src_connection() -> FileTransfer:
    # init source connection
    source_config = config['source']
    source_conn = init_connection(source_config)
    return source_conn


def init_target_connection() -> FileTransfer:
    # init target connection
    target_config = config['target']
    target_conn = init_connection(target_config)
    return target_conn


def detect_new_files(ti: Context) -> None:
    source_conn: FileTransfer = init_src_connection()
    target_conn: FileTransfer = init_target_connection()
    # list all files from source connection
    file_list = source_conn.list_all_files()
    # detect new files
    process_files = target_conn.detect_new_files(file_list)
    ti.xcom_push(key='process_files', value=process_files)
    # close connections
    source_conn.close()
    target_conn.close()


def download_files(ti: Context) -> None:
    process_files = ti.xcom_pull(task_ids='detect_new_files', key='process_files')
    if not process_files:
        raise AirflowSkipException('There is no new file to process')
    source_conn: FileTransfer = init_src_connection()
    # set process files for source connection
    source_conn.process_files = process_files
    # download files from source
    source_conn.download_files()
    # close connection
    source_conn.close()


def transform() -> None:
    # transform step before loading to destination
    pass


def put_files(ti: Context) -> None:
    process_files = ti.xcom_pull(task_ids='detect_new_files', key='process_files')
    target_conn: FileTransfer = init_target_connection()
    # set process files for target connection
    target_conn.process_files = process_files
    # put files to target
    target_conn.put_files()
    # close connection
    target_conn.close()


schedule_interval = config['schedule_interval'] if config['schedule_interval'] != 'None' else None

with DAG(
        dag_id=config['job_name'],
        schedule_interval=schedule_interval,
        start_date=days_ago(1),
        catchup=False,
) as dag:
    detect_new_files_task = PythonOperator(
        task_id='detect_new_files',
        python_callable=detect_new_files
    )

    download_files_task = PythonOperator(
        task_id='download_files',
        python_callable=download_files
    )

    transform_task = PythonOperator(
        task_id='transform',
        python_callable=transform
    )

    put_files_task = PythonOperator(
        task_id='put_files',
        python_callable=put_files
    )

    tasks = detect_new_files_task >> download_files_task >> transform_task >> put_files_task
