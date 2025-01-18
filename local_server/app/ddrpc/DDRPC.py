import asyncio, uuid, json
from typing import MutableMapping

from aio_pika import Message, connect
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractIncomingMessage, AbstractQueue, AbstractExchange
from aio_pika.exceptions import ChannelClosed

class DDRPCClient:
    connection: AbstractConnection
    channel: AbstractChannel
    callback_queue: AbstractQueue

    def __init__(self) -> None:
        self.futures: MutableMapping[str, asyncio.Future] = {}
    
    async def connect(self, amqp_server: str = "amqp://guest:guest@localhost/") -> "DDRPCClient":
        self.connection = await connect(amqp_server)
        self.channel = await self.connection.channel()
        self.callback_queue = await self.channel.declare_queue(name="rpc_callback_"+str(uuid.uuid4()),exclusive=True,auto_delete=True)
        await self.callback_queue.consume(self.response, no_ack=True)

    async def close(self) -> None:
        await self.channel.close()
        await self.connection.close()

    async def response(self, message: AbstractIncomingMessage) -> str:
        if message.correlation_id is None:
            raise MessageCorrelationException()
        
        future: asyncio.Future = self.futures.pop(message.correlation_id)
        future.set_result(message.body)

    async def check_queue(self, destination: str) -> bool:
        try:
            await self.channel.declare_queue("rpc_"+destination, passive=True)
            return True
        except ChannelClosed as e:
            if("RESOURCE_LOCKED" in e.args[0]):
                return True
            return False
        except Exception as e:
            return False
        return False

    async def call(self, destination: str, message: dict, tmout:int=5, prio:int=2) -> dict:
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        self.futures[correlation_id] = future
        try:
            msg_encoded = str(message).encode()
        except Exception as e:
            print(e)

        await self.channel.default_exchange.publish(
            Message(
                msg_encoded,
                content_type="text/plain",
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
                priority=prio
            ),
            routing_key="rpc_"+str(destination),
        )

        try:
            j = await asyncio.wait_for(future, timeout=tmout)
            return json.loads(j)
        except asyncio.TimeoutError:
            raise AssertionError('Queue is closed.')


class DDRPCServer:
    connection: AbstractConnection
    channel: AbstractChannel
    queue: AbstractQueue
    exchange: AbstractExchange
    server_id: str

    async def connect(self, server_id, rpc_host: str = "amqp://guest:guest@localhost/") -> None:
        self.server_id = server_id
        self.connection = await connect(rpc_host)
        self.channel = await self.connection.channel()
        self.exchange = self.channel.default_exchange

        self.queue = await self.channel.declare_queue("rpc_"+str(server_id), auto_delete=True, exclusive=True, arguments={'x-max-priority':3})
        print("Awaiting RPC requests")

    async def new_message(self,message: AbstractIncomingMessage, func) -> None:
        try:
            async with message.process(requeue=False):
                assert message.reply_to is not None

                jsn = json.loads(message.body.decode().replace('\'',"\""))

                assert type(jsn) is dict

                return_dict = {
                    "status":"ERR",
                    "code":"401",
                    "exception":"Wrong address"
                }

                return_dict = await func(jsn, self.server_id)

                assert type(return_dict) == dict
                
                ##### json feldolgozasa / utasitas valaszolasa
                response = str(json.dumps(return_dict)).encode()
                print("  | response ready "+str(json.dumps(return_dict))+"") if len(response) <= 2000 else print('  | response ready (too long to display)')

                await self.exchange.publish(
                    Message(
                        body=response,
                        correlation_id=message.correlation_id
                    ),
                    routing_key=message.reply_to,
                )
                print("  | request completed")
        except Exception:
            raise MessageProcessException()


class MessageProcessException(Exception):
    pass
class MessageCorrelationException(Exception):
    pass