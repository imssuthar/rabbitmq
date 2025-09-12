import pika
import sys

def send_message(message):
    try:
        conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        ch = conn.channel()
        
        # Create dead letter exchange and queue (same as consumer)
        ch.exchange_declare(exchange='dlx', exchange_type='direct', durable=True)
        ch.queue_declare(queue='dlq', durable=True, arguments={
            'x-queue-type': 'quorum'
        })
        ch.queue_bind(exchange='dlx', queue='dlq', routing_key='dlq')
        
        # Declare the same queue as consumer
        ch.queue_declare(queue='test.q', durable=True, arguments={
            'x-queue-type': 'quorum',
            'x-message-ttl': 60000,  # 10 minutes in milliseconds
            'x-max-length': 1000,     # Max 1000 messages in queue
            'x-overflow': 'reject-publish',  # Reject new messages when full
            'x-dead-letter-exchange': 'dlx',  # Route expired messages to DLX
            'x-dead-letter-routing-key': 'dlq'  # Route to DLQ
        })
        
        ch.basic_publish(
            exchange='',  # default exchange
            routing_key='test.q',  # route directly to queue
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)  # persistent
        )
        
        print(f" [x] Sent '{message}'")
        conn.close()
        return True
        
    except pika.exceptions.UnroutableError:
        print(" [ERROR] Message was rejected - queue might be full (max 1000 messages)")
        return False
    except Exception as e:
        print(f" [ERROR] Failed to send message: {e}")
        return False

# Test with different message sizes
if __name__ == "__main__":
    # Test 1: Normal message
    print("=== Test 1: Normal message ===")
    send_message("Hello Rabbit!")
    