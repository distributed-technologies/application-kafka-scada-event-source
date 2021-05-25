from time import sleep
from json import dumps,loads
from kafka import KafkaProducer
from kafka import KafkaConsumer
import sys
import datetime
import pyarrow as pa
import pyarrow.parquet as pq
import json

broker=str(sys.argv[1])
consume_topic=str(sys.argv[2])
produce_topic=str(sys.argv[3])

consumer = KafkaConsumer(
     consume_topic,
     bootstrap_servers=[broker],
     auto_offset_reset='earliest')

producer = KafkaProducer(bootstrap_servers=[broker],
                         value_serializer=lambda x: 
                         dumps(x).encode('utf-8'),
                         client_id="scada-json-producer")

for message in consumer:
    # Read the kafka record as raw bytes and transform to a pandas dataframe 
    reader = pa.BufferReader(message.value)
    table = pq.read_table(reader)
    df = table.to_pandas()
    for index,row in df.iterrows():
          # We dump the row to json and load to get the correct time format
          payload = row.to_json()
          timestamp = json.loads(payload)['timestamp']
          producer.send(topic=produce_topic, value=payload, timestamp_ms=timestamp)
          # We sleep 1 second to simulate scada event stream
          sleep(1)
