import json


def load_job_configs():
    job_configs: list[dict] = []
    with open('airflow-repo/scripts/configs/job_configs.json', 'r') as f:
        configs: dict = json.load(f)

    with open('airflow-repo/scripts/configs/source_configs.json', 'r') as s:
        source_configs: dict = json.load(s)

    for job_name in configs:
        job_config = configs[job_name]
        source_name = job_config['source_name']
        source_config = source_configs[source_name]

        target_name = job_config['target_name']
        target_config = source_configs[target_name]

        job_configs.append({
            'job_name': job_name,
            'source_name': source_name,
            'source_type': source_config['type'],
            'source_host': source_config['host'],
            'source_port': source_config['port'],
            'source_user': source_config['user'],
            'source_password': source_config['password'],
            'source_path': job_config['source_path'],
            'target_name': target_name,
            'target_type': target_config['type'],
            'target_host': target_config['host'],
            'target_port': target_config['port'],
            'target_user': target_config['user'],
            'target_password': target_config['password'],
            'target_path': job_config['target_path'],
            'schedule_interval': job_config['schedule_interval']
        })
    return job_configs


if __name__ == '__main__':
    job_configs = load_job_configs()
    for job_config in job_configs:
        base_dag = 'airflow-repo/dags/sync_file/base_sync_files.py.tpl'
        with open(base_dag, 'r') as file:
            template_content = file.read()
            config = json.dumps(job_config)
            job_name = job_config['job_name']
            rendered_content = template_content.replace(
                '{{ config }}', f"{config}")
        with open(f"airflow-repo/dags/sync_file/{job_name}.py", mode='w+', encoding='utf-8-sig') as file:
            file.write(rendered_content)
