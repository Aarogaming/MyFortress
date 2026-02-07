import asyncio
import json
import logging
import time
from concurrent import futures

import grpc
from artifacts.api import homegateway_pb2, homegateway_pb2_grpc
from gateway.config import Settings
from gateway.integrations.frigate import FrigateClient
from gateway.integrations.home_assistant import HomeMerlinClient

logger = logging.getLogger(__name__)


class MyFortressServicer(homegateway_pb2_grpc.MyFortressServicer):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def Health(self, request, context):
        return homegateway_pb2.HealthResponse(status="ok")

    async def ProbeHomeMerlin(self, request, context):
        client = HomeMerlinClient(
            settings=self.settings,
            base_url=request.base_url or self.settings.home_assistant_url,
            token=request.token or self.settings.home_assistant_token,
            verify_ssl=request.verify_ssl,
        )
        res = await client.probe_entities(list(request.entities))
        readings = {}
        for eid, r in res.readings.items():
            readings[eid] = homegateway_pb2.HomeMerlinReading(
                entity_id=r.entity_id,
                state=str(r.state),
                attributes={k: str(v) for k, v in r.attributes.items()},
                error=r.error or "",
            )
        return homegateway_pb2.HomeMerlinProbeResponse(
            healthy=res.healthy, readings=readings, error=res.error or ""
        )

    async def HomeMerlinService(self, request, context):
        client = HomeMerlinClient(
            settings=self.settings,
            base_url=request.base_url or self.settings.home_assistant_url,
            token=request.token or self.settings.home_assistant_token,
        )
        data = json.loads(request.data_json) if request.data_json else {}
        res = await client.call_service(request.domain, request.service, data)
        return homegateway_pb2.HomeMerlinServiceResponse(
            success=res.success,
            response_json=json.dumps(res.response),
            error=res.error or "",
        )

    async def HomeMerlinState(self, request, context):
        client = HomeMerlinClient(
            settings=self.settings,
            base_url=request.base_url or self.settings.home_assistant_url,
            token=request.token or self.settings.home_assistant_token,
        )
        state = json.loads(request.state_json) if request.state_json else None
        attrs = json.loads(request.attributes_json) if request.attributes_json else {}
        res = await client.set_state(request.entity_id, state, attrs)
        return homegateway_pb2.HomeMerlinStateResponse(
            success=res.success,
            state_json=json.dumps(res.state),
            attributes_json=json.dumps(res.attributes),
            error=res.error or "",
        )

    async def ProbeFrigate(self, request, context):
        client = FrigateClient(
            settings=self.settings,
            base_url=request.base_url or self.settings.frigate_url,
            api_key=request.api_key or self.settings.frigate_api_key,
        )
        res = await client.fetch_version()
        return homegateway_pb2.FrigateProbeResponse(
            healthy=res.healthy,
            version=res.version or "",
            version_json=json.dumps(res.raw),
            error=res.error or "",
            cameras=res.cameras,
        )

    async def FrigateEvents(self, request, context):
        client = FrigateClient(
            settings=self.settings,
            base_url=request.base_url or self.settings.frigate_url,
            api_key=request.api_key or self.settings.frigate_api_key,
        )
        res = await client.fetch_events(limit=request.limit or 50)
        return homegateway_pb2.FrigateEventsResponse(
            success=res.get("success", True),
            events_json=json.dumps(res.get("events", [])),
            error=res.get("error", ""),
        )

    async def Snapshot(self, request, context):
        # Simplified snapshot for gRPC baseline
        ha_json = "{}"
        fr_json = "{}"

        if request.include_home_assistant:
            client = HomeMerlinClient(settings=self.settings)
            res = await client.probe_entities(list(request.home_assistant_entities))
            ha_json = json.dumps(res.model_dump())

        if request.include_frigate:
            client = FrigateClient(settings=self.settings)
            if request.include_frigate_cameras:
                res = await client.fetch_snapshot()
            else:
                res = await client.fetch_version()
            fr_json = json.dumps(res.model_dump())

        return homegateway_pb2.SnapshotResponse(
            home_assistant_json=ha_json, frigate_json=fr_json
        )


class AuthInterceptor(grpc.aio.ServerInterceptor):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def intercept_service(self, continuation, handler_call_details):
        if not self.api_key:
            return await continuation(handler_call_details)

        metadata = dict(handler_call_details.invocation_metadata)
        if metadata.get("x-api-key") != self.api_key:

            async def abort(request, context):
                await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid API key")

            return grpc.unary_unary_rpc_method_handler(abort)

        return await continuation(handler_call_details)


async def serve_grpc(settings: Settings):
    interceptors = []
    if settings.api_key:
        interceptors.append(AuthInterceptor(settings.api_key))

    server = grpc.aio.server(interceptors=interceptors)
    homegateway_pb2_grpc.add_MyFortressServicer_to_server(
        MyFortressServicer(settings), server
    )
    listen_addr = f"[::]:{settings.port + 1}"
    server.add_insecure_port(listen_addr)
    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()
    await server.wait_for_termination()
