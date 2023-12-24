from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.email_operator import EmailOperator
from airflow.sensors.filesystem import FileSensor
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.models import Variable
from airflow.utils_task_group import TaskGroup
from datetime import datetime, timedelta
import json
import os

default_args = {
    'depends_on_past': False,
    'email': ['my_email@email.com.br'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=10)
}

dag = DAG("windturbine", description="Dados da Turbina",
          schedule_interval=None, start_date=datetime(2023, 12, 23),
          catchup=False, default_args=default_args, default_view='graph',
          doc_md='## Dag para registrar dados da turbina eólica')

group_check_temp = TaskGroup('group_check_temp', dag=dag)
group_database = TaskGroup('group_database', dag=dag)

file_sensor_task = FileSensor(
    task_id='file_sensor_task',
    file_path=Variable.get('path_file'),
    fs_conn_id='fs_default',
    poke_interval=10,
    dag=dag
)


def process_file(**kwargs):
    with open(Variable.get('path_file')) as f:
        data = json.load(f)
        kwargs['ti'].xcom.push(key='idtemp',value=data['idtemp'])
        kwargs['ti'].xcom.push(key='powerfactor', value=data['powerfactor'])
        kwargs['ti'].xcom.push(key='hydraulicpressure', value=data['hydraulicpressure'])
        kwargs['ti'].xcom.push(key='temperature', value=data['temperature'])
        kwargs['ti'].xcom.push(key='timestamp', value=data['timestamp'])
    os.remove(Variable.get('path_file'))


get_data = PythonOperator(
    task_id='get_data',
    python_callable=process_file,
    provide_context=True,
    dag=dag
)

create_table = PostgresOperator(
    task_id='create_table',
    postgres_conn_id='postgres',
    sql='''CREATE TABLE IF NOT EXISTS
    sensors (idtemp varchar, powerfactor varchar, 
    hydraulicpressure varchar, temperature varchar,
    timestamp varchar);
    ''',
    task_group='group_database',
    dag=dag
)


insert_data = PostgresOperator(
    task_id='insert_data',
    postgres_conn_id='postgres',
    parameters=(
        '{{ ti.xconn_pull(task_ids="get_data", key="idtemp") }}',
        '{{ ti.xconn_pull(task_ids="get_data", key="powerfactor") }}',
        '{{ ti.xconn_pull(task_ids="get_data", key="hydraulicpressure") }}',
        '{{ ti.xconn_pull(task_ids="get_data", key="temperature") }}',
        '{{ ti.xconn_pull(task_ids="get_data", key="timestamp") }}'
    ),
    sql='''
        INSERT INTO sensors (idtemp, powerfactor, hydraulicpressure, temperature, timestamp") }}') 
        VALUES (%s, %s, %s, %s, %s)
    ''',
    task_group='group_database',
    dag=dag
)

send_email_alert = EmailOperator(
    task_id='send_email_alert',
    to='my_email@email.com.br',
    subject='Airflow alert',
    html_content='''
        <h3>Alerta de Temperatura</h3>
        <p>Dag: windturbine</p>
    ''',
    task_group='group_check_temp',
    dag=dag
)


send_email_normal = EmailOperator(
    task_id='send_email_normal',
    to='my_email@email.com.br',
    subject='Airflow advise',
    html_content='''
        <h3>Temperaturas normais</h3>
        <p>Dag: windturbine</p>
    ''',
    task_group='group_check_temp',
    dag=dag
)


def avalia_temp(**context):
    number = float(context['ti'].xconn.pull(task_ids='get_data', key='temperature'))
    if number >= 24:
        return 'group_check_temp.send_email_alert'
    else:
        return 'group_check_temp.send_email_normal'


check_temp_branch = BranchPythonOperator(
    task_id='check_temp_branch',
    python_callable=avalia_temp,
    provide_context=True,
    task_group='group_check_temp',
    dag=dag
)

with group_check_temp:
    check_temp_branch >> [send_email_alert, send_email_normal]


with group_database:
    create_table >> insert_data


file_sensor_task >> get_data
get_data >> group_check_temp
get_data >> group_database
