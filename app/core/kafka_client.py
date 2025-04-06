import logging

from confluent_kafka import KafkaException, Producer
from sqlmodel import SQLModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class KafkaClient:
    def __init__(self):
        self._producer: Producer | None = None


    def acked(self, err, msg):
        """
        Callback function executed by Kafka Producer once a message is delivered or fails.
        Triggered by poll() or flush().
        """
        if err is not None:
            logger.error(f"Failed to deliver message: {err}")
        else:
            logger.info(
                f"Message produced: '{msg.topic()}' "
                f"[Partition {msg.partition()}] @ Offset {msg.offset()}"
            )


    def init_producer(self):
        """
        Initializes the Kafka Producer instance using settings.
        """
        conf = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': settings.KAFKA_CLIENT_ID,
            'acks': 'all',  # Wait for all in-sync replicas to acknowledge receipt
            'retries': 3,  # Number of retries on failure
            'retry.backoff.ms': 1000,  # Time to wait between retries
            'enable.idempotence': True,  # Prevents duplicate messages from producer retries
        }
        try:
            self._producer = Producer(conf)
            logger.info(
                f"Kafka producer initialized successfully."
                f" Brokers: {settings.KAFKA_BOOTSTRAP_SERVERS}"
            )
        except KafkaException as e:
            logger.exception(f"CRITICAL: Failed to initialize Kafka producer: {e}", exc_info=True)
            self._producer = None # Ensure producer is None if init fails
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred "
                f"during Kafka producer initialization: {e}", exc_info=True
            )
            self._producer = None


    def close_producer(self):
        """
        Flushes any buffered messages and closes the Kafka Producer.
        Should be called on application shutdown.
        """
        if not self._producer:
            return

        logger.info("Flushing Kafka producer...")
        try:
            remaining_messages = self._producer.flush(timeout=10)
            if remaining_messages > 0:
                logger.warning(
                    f"Kafka producer flush timed out, {remaining_messages}"
                    f" messages may not have been sent."
                )
            else:
                logger.info("Kafka producer flushed successfully.")
        except Exception as e:
            logger.exception(f"Error flushing Kafka producer: {e}", exc_info=True)


    def produce_message(self, topic: str, event: SQLModel):
        """
        Produces (sends) a Pydantic event model to the specified Kafka topic.

        Args:
            topic (str): The Kafka topic to send the message to.
            event (BaseModel): The Pydantic model instance representing the event.
        """
        if not self._producer:
            logger.error("Kafka producer not initialized")
            return False

        try:
            message_bytes = event.model_dump_json().encode('utf-8')

            key_bytes = None
            if hasattr(event, 'user_id') and event.user_id:
                try:
                    key_bytes = str(event.user_id).encode('utf-8')
                except AttributeError:
                    logger.warning(
                        "Event model has user_id but couldn't convert to string for Kafka key."
                    )

            self._producer.produce(
                topic=topic,
                value=message_bytes,
                key=key_bytes,
                callback=self.acked
            )

            self._producer.poll(0)

            logger.info(
                f"Message produced to Kafka topic '{topic}'."
                f" Key: {key_bytes.decode('utf-8') if key_bytes else 'None'}"
            )
            return True

        except BufferError as e:
            logger.error(f"Kafka producer queue is full: {e}", exc_info=True)
            return False
        except KafkaException as e:
            logger.error(f"KafkaException while producing message: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error producing message to Kafka: {e}", exc_info=True)
            return False


kafka_client = KafkaClient()
