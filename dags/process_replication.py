from datetime import datetime
from time import sleep
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
import json 
from kafka import KafkaProducer
from kafka import KafkaConsumer

   
def load_json_data_kafka(**kwargs):
    print('Sending messages to the broker')
    
    topic_name = kwargs.get('topic_name')
    data_path = kwargs.get('data_path')
    
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        api_version=(0,10,2),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    with open(data_path) as json_file:
        messages = json.load(json_file)

    counter = 0
    for message in messages:
        counter+=1
        producer.send(topic_name, message)
        if counter == 1000:
            counter=0
            producer.flush()
            sleep(3)
    print('All data was sent')
    return

import time
import datetime

def convert(str_date):
    return  int(time.mktime(datetime.datetime.strptime(str_date,'%m/%d/%Y %H:%M:%S').timetuple()))



def consume_topic(**kwargs):
    topic_src = kwargs.get('topic_src')
    topic_tgt = kwargs.get('topic_tgt')
    
    consumer = KafkaConsumer(
        topic_src,
        bootstrap_servers=['kafka:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='my-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
     )
    
    time_begin = convert('04/14/2021 11:00:00')
    time_end = convert('04/14/2021 13:00:00')


    while True:
        for msg in consumer:
            if msg.value['timestamp'] >= time_begin and msg.value['timestamp'] <= time_end:
                load_msg_kafka(msg,topic_tgt)
                print(type( msg.value), msg.value)
     
def convert(str_date):
    return  int(time.mktime(datetime.datetime.strptime(str_date,'%m/%d/%Y %H:%M:%S').timetuple()))
    
def load_msg_kafka(message, topic_name):

    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        api_version=(0,10,2),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )    
    producer.send(topic_name, message)
    producer.flush()
    return

with DAG(dag_id='process_replication',
         default_args={'owner': 'airflow'},
         schedule_interval="@once",
         start_date=days_ago(2),
         tags=['etl', 'action', 'user']) as dag:

    execution_date = '{{ ds }}'
    
    load_json_data_kafka = PythonOperator(
        task_id='load_json_data_kafka',
        python_callable=load_json_data_kafka,
        op_kwargs={
            'data_path': '/opt/airflow/data/action_data.json',
            'topic_name': 'topic-a'
        }
    )
        
    consume_topic_a = PythonOperator(
        task_id='consume_topic_a',
        python_callable=consume_topic,
        op_kwargs={
            'topic_src': 'topic-a',
            'topic_tgt':'topic-b'
        }
    )   
    
    [load_json_data_kafka,consume_topic_a]




