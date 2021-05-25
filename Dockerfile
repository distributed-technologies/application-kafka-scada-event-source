FROM "python:3.7-slim-buster"

RUN pip install kafka-python
RUN pip install pyarrow
RUN pip install pandas

COPY scripts/scada_parquet_transformer.py /app/

ENTRYPOINT ["sh"] 
