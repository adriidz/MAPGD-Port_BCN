# mqtt_client.py
import json
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder

class AWSClient:
    def __init__(self, endpoint, cert_path, key_path, root_ca_path, client_id="test_tracker"):
        self.endpoint = endpoint
        self.client_id = client_id
        
        # Configuración de la conexión segura
        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

        self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.endpoint,
            cert_filepath=cert_path,
            pri_key_filepath=key_path,
            client_bootstrap=client_bootstrap,
            ca_filepath=root_ca_path,
            on_connection_interrupted=self.on_interrupted,
            on_connection_resumed=self.on_resumed,
            client_id=self.client_id,
            clean_session=False,
            keep_alive_secs=30
        )

    def connect(self):
        print(f"Conectando a AWS IoT Core en {self.endpoint}...")
        connect_future = self.mqtt_connection.connect()
        connect_future.result() # Esperar a que conecte
        print("Conectado!")

    def publish_event(self, topic, data):
        payload = json.dumps(data)
        self.mqtt_connection.publish(
            topic=topic,
            payload=payload,
            qos=mqtt.QoS.AT_LEAST_ONCE
        )
        # Opcional: imprimir para debug
        # print(f"Enviado a {topic}: {payload}")

    def on_interrupted(self, connection, error, **kwargs):
        print(f"Conexión interrumpida. error: {error}")

    def on_resumed(self, connection, return_code, session_present, **kwargs):
        print(f"Conexión reestablecida. return_code: {return_code}")