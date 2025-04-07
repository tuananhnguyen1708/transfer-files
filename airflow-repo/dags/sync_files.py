from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.utils.context import Context
from airflow.exceptions import AirflowSkipException
from file_transfer_module.file_transfer import FileTransfer
from file_transfer_module.sftp_file_transfer import SFTPFileTransfer

config = {
    'source_host': '192.168.1.3',
    'source_port': 2222,
    'source_user': 'sftp1',
    'source_password': '123456',
    'source_path': '/',
    'target_host': '192.168.1.3',
    'target_port': 2223,
    'target_user': 'sftp2',
    'target_password': '123456',
    'target_path': '/',
}


def init_src_connection() -> FileTransfer:
    # init source SFTP connection
    source_conn = SFTPFileTransfer(host=config['source_host'], port=config['source_port'],
                                   username=config['source_user'],
                                   password=config['source_password'], root_path=config['source_path'])
    return source_conn


def init_target_connection() -> FileTransfer:
    # init target SFTP connection
    target_conn = SFTPFileTransfer(host=config['target_host'], port=config['target_port'], username=config['target_user'],
                                 password=config['target_password'], root_path=config['target_path'])
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


def put_files(ti: Context) -> None:
    process_files = ti.xcom_pull(task_ids='detect_new_files', key='process_files')
    target_conn: FileTransfer = init_target_connection()
    # set process files for target connection
    target_conn.process_files = process_files
    # put files to target
    target_conn.put_files()
    # close connection
    target_conn.close()


with DAG(
        dag_id='sync_files',
        schedule_interval=None,
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

    put_files_task = PythonOperator(
        task_id='put_files',
        python_callable=put_files
    )

    tasks = detect_new_files_task >> download_files_task >> put_files_task
