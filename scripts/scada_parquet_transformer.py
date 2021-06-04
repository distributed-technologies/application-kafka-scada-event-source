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
consumer_group=None

if len(sys.argv)>3:
      consumer_group=str(sys.argv[4])

consumer = KafkaConsumer(
     consume_topic,
     bootstrap_servers=[broker],
     auto_offset_reset='earliest',
     group_id=consumer_group)

producer = KafkaProducer(bootstrap_servers=[broker],
            value_serializer=lambda x: 
            dumps(x).encode('utf-8'))
print(f"Contacted broker: {broker}")
print(f"Started consuming from topic: {consume_topic}")
print(f"Started producing on topic: {produce_topic}")
for message in consumer:
    # Read the kafka record as raw bytes and transform to a pandas dataframe 
    reader = pa.BufferReader(message.value)
    df = pq.read_table(reader).to_pandas() 
    lines_in_file = len(df)
    print(f"Read parquet file with {lines_in_file} lines from topic: {consume_topic}" )
    for index,row in df.iterrows():
          # We dump the row to json and load to get the correct time format
          payload_string = row.to_json()
          payload = json.loads(payload_string)
          timestamp = payload['timestamp']
          producer.send(topic=produce_topic, value=payload, timestamp_ms=timestamp)
          # We sleep 1 second to simulate scada event stream
          sleep(1)
    print(f"Finished writing {lines_in_file} events to topic: {produce_topic}")
