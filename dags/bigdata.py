from airflow import DAG
from datetime import datetime
from bigdata_operator import BigDataOperator  # importando plugin normalmente como qualquer outro

dag = DAG("bigdata", description="Bigdata DAG With Plugin", schedule_interval=None, start_date=datetime(2023,12,18),
          catchup=False)

bigdata = BigDataOperator(task_id="tsk1", path_to_csv_file="./", path_to_save_file="./",
                          separator='', file_type='parquet', dag=dag)

bigdata

