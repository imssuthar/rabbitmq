import pika, time

conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
ch = conn.channel()

def callback(ch_, method, properties, body):
    print(" [x] Received:", body.decode())
    # simulate forgetting to ACK - message will go to DLQ after 10 minutes
    # ch_.basic_ack(delivery_tag=method.delivery_tag)
    # time.sleep(20)
    print(" [!] Done processing but not ACKed - will go to DLQ after 10 minutes")

def dlq_callback(ch_, method, properties, body):
    print(" [DLQ] Received dead letter:", body.decode())
    ch_.basic_ack(delivery_tag=method.delivery_tag)

# Create dead letter exchange and queue
ch.exchange_declare(exchange='dlx', exchange_type='direct', durable=True)
ch.queue_declare(queue='dlq', durable=True, arguments={
    'x-queue-type': 'quorum'
})

# Bind DLQ to DLX
ch.queue_bind(exchange='dlx', queue='dlq', routing_key='dlq')

# Set up main queue with DLQ configuration
ch.queue_declare(queue='test.q', durable=True, arguments={
    'x-queue-type': 'quorum',
    'x-message-ttl': 60000,  # 10 minutes in milliseconds
    'x-max-length': 1000,     # Max 1000 messages in queue
    'x-overflow': 'reject-publish',  # Reject new messages when full
    'x-dead-letter-exchange': 'dlx',  # Route expired messages to DLX
    'x-dead-letter-routing-key': 'dlq'  # Route to DLQ
})

ch.basic_qos(prefetch_count=5)  # limit inflight
ch.basic_consume(queue='test.q', on_message_callback=callback, auto_ack=False)
# ch.basic_consume(queue='dlq', on_message_callback=dlq_callback, auto_ack=False)

print(" [*] Waiting for messages. To exit press CTRL+C")
print(" [*] Main queue: test.q (max 1000 msgs, 10min TTL)")
ch.start_consuming()