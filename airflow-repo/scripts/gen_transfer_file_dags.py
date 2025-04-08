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
            'source': {
                'name': source_name,
                'type': source_config['type'],
                'host': source_config['host'],
                'port': source_config['port'],
                'user': source_config['user'],
                'password': source_config['password'],
                'path': job_config['source_path'],
            },
            'target': {
                'name': target_name,
                'type': target_config['type'],
                'host': target_config['host'],
                'port': target_config['port'],
                'user': target_config['user'],
                'password': target_config['password'],
                'path': job_config['target_path'],
            },
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
