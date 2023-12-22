from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime

dag = DAG("trigger_dag2", description="Minha trigger DAG", schedule_interval=None, start_date=datetime(2023, 12, 18),
          catchup=False)

task1 = BashOperator(task_id="tsk1", bash_command="exit 1", dag=dag)  # exit 1 para forcar task a falhar
task2 = BashOperator(task_id="tsk2", bash_command="sleep 5", dag=dag)
task3 = BashOperator(task_id="tsk3", bash_command="sleep 5", dag=dag, trigger_rule="one_failed")
# task 3 sera executada pois a task 1 ira falhar

[task1, task2] >> task3 # precedencia

