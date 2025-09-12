# RabbitMQ Fundamentals & Best Practices

## 📋 Table of Contents
1. [Core Architecture](#core-architecture)
2. [Message Flow](#message-flow)
3. [Queue Types](#queue-types)
4. [Exchange Types](#exchange-types)
5. [Bindings & Routing](#bindings--routing)
6. [Dead Letter Queues (DLQ)](#dead-letter-queues-dlq)
7. [Queue Configuration](#queue-configuration)
8. [Consumer Patterns](#consumer-patterns)
9. [Best Practices](#best-practices)
10. [Commands Reference](#commands-reference)

---

## 🏗️ Core Architecture

### Components
- **Producer**: Sends messages to exchanges
- **Exchange**: Routes messages based on routing rules
- **Queue**: Stores messages for consumers
- **Consumer**: Processes messages from queues
- **Binding**: Links exchanges to queues with routing rules

### Key Concepts
- **Connection**: Physical TCP connection to RabbitMQ broker
- **Channel**: Logical connection within a physical connection (lightweight)
- **VHost**: Virtual host for logical separation

---

## 🔄 Message Flow

### Standard Flow
```
Producer → Exchange → Binding → Queue → Consumer
```

### Important Notes
- **Producers publish to exchanges, NOT queues directly**
- **Exchanges route messages to queues based on bindings**
- **Consumers consume from queues**

### Example
```python
# Producer publishes to exchange
ch.basic_publish(
    exchange='orders.exchange',  # Exchange name
    routing_key='order.created', # Routing key
    body='Order data'
)

# Binding routes to queue
ch.queue_bind(
    exchange='orders.exchange',
    queue='order.processing',
    routing_key='order.created'
)
```

---

## 📦 Queue Types

### 1. Classic Queues (Default)
```python
ch.queue_declare(queue='classic_queue', durable=True)
```
- **Use Case**: Simple, single-node applications
- **Durability**: Optional
- **Replication**: None

### 2. Quorum Queues ⭐ (Recommended)
```python
ch.queue_declare(queue='quorum_queue', durable=True, arguments={
    'x-queue-type': 'quorum'
})
```
- **Use Case**: High availability, data safety
- **Durability**: Always durable
- **Replication**: Multi-node with Raft consensus
- **Benefits**: Survives node failures, strong consistency

### 3. Stream Queues
```python
ch.queue_declare(queue='stream_queue', durable=True, arguments={
    'x-queue-type': 'stream'
})
```
- **Use Case**: High-throughput, time-series data
- **Performance**: Very high throughput
- **Features**: Consumer groups, retention policies

---

## 🔀 Exchange Types

### 1. Direct Exchange
```python
ch.exchange_declare(exchange='direct.ex', exchange_type='direct')
```
- **Routing**: Exact match on routing key
- **Use Case**: Point-to-point messaging

### 2. Topic Exchange
```python
ch.exchange_declare(exchange='topic.ex', exchange_type='topic')
```
- **Routing**: Pattern matching with wildcards
- **Use Case**: Complex routing scenarios

### 3. Fanout Exchange
```python
ch.exchange_declare(exchange='fanout.ex', exchange_type='fanout')
```
- **Routing**: Broadcasts to all bound queues
- **Use Case**: Notifications, events

### 4. Headers Exchange
```python
ch.exchange_declare(exchange='headers.ex', exchange_type='headers')
```
- **Routing**: Based on message headers
- **Use Case**: Complex routing logic

---

## 🔗 Bindings & Routing

### Multiple Queues, Same Routing Key
```python
# Analytics + Processing pattern
ch.queue_bind(exchange='orders.ex', queue='order.analytics', routing_key='order.created')
ch.queue_bind(exchange='orders.ex', queue='order.processing', routing_key='order.created')
ch.queue_bind(exchange='orders.ex', queue='order.notifications', routing_key='order.created')
```

**Benefits:**
- **Analytics**: Track all orders
- **Processing**: Handle business logic
- **Notifications**: Send alerts/emails

### Routing Key Patterns
```python
# Topic exchange examples
'order.created'     # Exact match
'order.*'          # Any order event
'*.created'        # Any created event
'order.#'          # All order events
```

---

## ⚰️ Dead Letter Queues (DLQ)

### Purpose
- Handle failed messages
- Prevent message loss
- Debug processing issues
- Retry mechanisms

### Configuration
```python
# Create DLX and DLQ
ch.exchange_declare(exchange='dlx', exchange_type='direct', durable=True)
ch.queue_declare(queue='dlq', durable=True, arguments={'x-queue-type': 'quorum'})
ch.queue_bind(exchange='dlx', queue='dlq', routing_key='dlq')

# Configure main queue with DLQ
ch.queue_declare(queue='main.queue', durable=True, arguments={
    'x-queue-type': 'quorum',
    'x-message-ttl': 600000,  # 10 minutes
    'x-dead-letter-exchange': 'dlx',
    'x-dead-letter-routing-key': 'dlq'
})
```

### DLQ Triggers
- **TTL Expiry**: Messages expire without being processed
- **Max Length**: Queue reaches maximum capacity
- **Rejection**: Consumer rejects message
- **Manual**: Explicitly send to DLQ

---

## ⚙️ Queue Configuration

### Essential Arguments
```python
ch.queue_declare(queue='configured.queue', durable=True, arguments={
    'x-queue-type': 'quorum',           # Queue type
    'x-message-ttl': 600000,            # Message TTL (10 minutes)
    'x-max-length': 1000,               # Max queue length
    'x-overflow': 'reject-publish',     # Overflow behavior
    'x-dead-letter-exchange': 'dlx',    # DLX for failed messages
    'x-dead-letter-routing-key': 'dlq'  # DLQ routing key
})
```

### Overflow Behaviors
- **`reject-publish`**: Reject new messages when full
- **`drop-head`**: Remove oldest messages when full

### TTL Configuration
- **Queue TTL**: `x-message-ttl` (milliseconds)
- **Message TTL**: Set per message in properties
- **Queue TTL**: `x-expires` (queue lifetime)

---

## 👥 Consumer Patterns

### Round-Robin Distribution
```python
# Multiple consumers on same queue
# Messages distributed evenly: 1→C1, 2→C2, 3→C3, 4→C1...
ch.basic_qos(prefetch_count=1)  # Process one at a time
```

### Prefetch Count
```python
ch.basic_qos(prefetch_count=5)  # Max 5 unacked messages
```
- **Low prefetch**: More even distribution
- **High prefetch**: Better throughput, potential uneven distribution

### Acknowledgment
```python
# Manual ACK (recommended)
ch.basic_consume(queue='test.q', on_message_callback=callback, auto_ack=False)

def callback(ch, method, properties, body):
    # Process message
    ch.basic_ack(delivery_tag=method.delivery_tag)
```

---

## 🎯 Best Practices

### 1. Queue Design
- **Use quorum queues** for production
- **Set appropriate TTL** to prevent message buildup
- **Configure DLQ** for error handling
- **Set queue limits** to prevent memory issues

### 2. Message Handling
- **Validate payload size** (e.g., 10KB limit)
- **Use manual ACK** for reliability
- **Handle failures gracefully**
- **Monitor queue depths**

### 3. Performance
- **Reuse connections**, create channels as needed
- **Set appropriate prefetch count**
- **Use separate channels** for different operations
- **Monitor memory usage**

### 4. Error Handling
- **Implement DLQ patterns**
- **Log failed messages**
- **Set up monitoring and alerting**
- **Plan retry strategies**

---

## 🛠️ Commands Reference

### Queue Management
```bash
# List queues with details
rabbitmqadmin list queues name type arguments consumers messages_ready messages_unacknowledged

# List exchanges
rabbitmqadmin list exchanges name type arguments

# List bindings
rabbitmqadmin list bindings source_name destination_name routing_key
```

### Queue Operations
```bash
# Delete queue
rabbitmqctl delete_queue queue_name

# Purge queue
rabbitmqctl purge_queue queue_name

# Get queue info
rabbitmqctl list_queues name type arguments
```

---

## 📊 Example: Complete Setup

### Producer
```python
import pika

def send_message(message, max_size_kb=10):
    # Validate payload size
    if len(message.encode('utf-8')) > max_size_kb * 1024:
        return False
    
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    ch = conn.channel()
    
    # Declare queue with DLQ configuration
    ch.queue_declare(queue='orders.queue', durable=True, arguments={
        'x-queue-type': 'quorum',
        'x-message-ttl': 600000,
        'x-max-length': 1000,
        'x-overflow': 'reject-publish',
        'x-dead-letter-exchange': 'dlx',
        'x-dead-letter-routing-key': 'dlq'
    })
    
    ch.basic_publish(
        exchange='',
        routing_key='orders.queue',
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    
    conn.close()
    return True
```

### Consumer
```python
import pika

def setup_consumer():
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    ch = conn.channel()
    
    # Setup DLQ
    ch.exchange_declare(exchange='dlx', exchange_type='direct', durable=True)
    ch.queue_declare(queue='dlq', durable=True, arguments={'x-queue-type': 'quorum'})
    ch.queue_bind(exchange='dlx', queue='dlq', routing_key='dlq')
    
    # Setup main queue
    ch.queue_declare(queue='orders.queue', durable=True, arguments={
        'x-queue-type': 'quorum',
        'x-message-ttl': 600000,
        'x-max-length': 1000,
        'x-overflow': 'reject-publish',
        'x-dead-letter-exchange': 'dlx',
        'x-dead-letter-routing-key': 'dlq'
    })
    
    def callback(ch, method, properties, body):
        print(f"Processing: {body.decode()}")
        # Process message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def dlq_callback(ch, method, properties, body):
        print(f"DLQ: {body.decode()}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    ch.basic_qos(prefetch_count=5)
    ch.basic_consume(queue='orders.queue', on_message_callback=callback, auto_ack=False)
    ch.basic_consume(queue='dlq', on_message_callback=dlq_callback, auto_ack=False)
    
    ch.start_consuming()
```

---

## 🚀 Key Takeaways

1. **Producers → Exchanges → Queues → Consumers**
2. **Use quorum queues for production reliability**
3. **Implement DLQ patterns for error handling**
4. **Configure TTL and queue limits**
5. **Use manual ACK for message reliability**
6. **Multiple queues can bind to same routing key**
7. **Round-robin distribution for load balancing**
8. **Monitor queue health and performance**

---

*This README covers the essential RabbitMQ concepts and patterns for building reliable, scalable message-driven applications.*
