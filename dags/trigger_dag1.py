from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime

dag = DAG("trigger_dag1", description="Minha trigger DAG", schedule_interval=None, start_date=datetime(2023, 12, 18),
          catchup=False)

task1 = BashOperator(task_id="tsk1", bash_command="sleep 5", dag=dag)
task2 = BashOperator(task_id="tsk2", bash_command="sleep 5", dag=dag)
task3 = BashOperator(task_id="tsk3", bash_command="sleep 5", dag=dag, trigger_rule="one_failed")
# task 3 sera skippada pois so iria executar se uma das tasks anteriores falhasse

[task1, task2] >> task3 # precedencia

