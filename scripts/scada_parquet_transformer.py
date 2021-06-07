from time import sleep
from json import dumps,loads
from kafka import KafkaProducer,KafkaConsumer,TopicPartition 
import sys
import datetime
import pyarrow as pa
import pyarrow.parquet as pq
import json

broker=str(sys.argv[1])
consume_topic=str(sys.argv[2])
produce_topic=str(sys.argv[3])
consume_interval=int(sys.argv[4])
topic_line_offset=str(sys.argv[5])
consumer_group=None

if len(sys.argv)>5:
      consumer_group=str(sys.argv[6])

consumer = KafkaConsumer(
     consume_topic,
     bootstrap_servers=[broker],
     auto_offset_reset='earliest',
     group_id=consumer_group)

offset_line_consumer = KafkaConsumer(
     topic_line_offset,
     bootstrap_servers=[broker],
     auto_offset_reset='earliest',
     value_deserializer=lambda x: loads(x.decode('utf-8')),
     group_id="consumer-offset")

producer = KafkaProducer(bootstrap_servers=[broker],
            value_serializer=lambda x: 
            dumps(x).encode('utf-8'))

print(f"Contacted broker: {broker}")
print(f"Started consuming from topic: {consume_topic}")
print(f"Started producing on topic: {produce_topic}")

# Manually assign partition to consumer.
partition = TopicPartition(topic_line_offset,0)
# offset_line_consumer.assign([partition])

end_offset =  offset_line_consumer.end_offsets([partition])[partition]
if end_offset == 0:
      print("Nothing in topic setting offset to 0")
      producer.send(topic=topic_line_offset,value=0,partition=0)
else:
      print(f"End offset: {end_offset}")

print("Fetching line number")
# Fetch the latest message in the topic
for message in offset_line_consumer:
      line_number = message.value
      print(f"got: {line_number}")
      if end_offset <= ( message.offset + 2 ):
            break
offset_line_consumer.commit()

print(f"Got line number offset {line_number}")
for message in consumer:
    # Read the kafka record as raw bytes and transform to a pandas dataframe 
    reader = pa.BufferReader(message.value)
    df = pq.read_table(reader).to_pandas() 
    lines_in_file = len(df)
    print(f"Read parquet file with {lines_in_file} lines from topic: {consume_topic}" )
    print(f"Producing from line: {line_number}")
    for index,row in df.iterrows():
          if index < (line_number + 1) :
                break

          # We dump the row to json and load to get the correct time format
          payload_string = row.to_json()
          payload = json.loads(payload_string)
          producer.send(topic=produce_topic, value=payload)
          producer.send(topic=topic_line_offset,value=index)
          
          # We sleep 1 second to simulate scada event stream
          sleep(consume_interval)
    print(f"Finished writing {lines_in_file} events to topic: {produce_topic}")
