#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#
import os
import sys

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.services.gemini_multimodal_live import GeminiMultimodalLiveLLMService
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)


from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.pipeline.runner import PipelineRunner
from pipecat.frames.frames import Frame, TextFrame
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.minimax.tts import MiniMaxHttpTTSService
from pipecat.services.assemblyai.stt import AssemblyAISTTService, AssemblyAIConnectionParams
from pipecat.services.groq.stt import GroqSTTService
from pipecat.services.gladia.stt import GladiaSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openrouter.llm import OpenRouterLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams
from pipecat.transports.services.daily import DailyParams
from pipecat.transcriptions.language import Language
from pipecat.services.gladia.config import (
    GladiaInputParams,
    LanguageConfig,
    RealtimeProcessingConfig
)

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")


async def run_bot(websocket_client):
    ws_transport = FastAPIWebsocketTransport(
        websocket=websocket_client,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=SileroVADAnalyzer(),
            serializer=ProtobufFrameSerializer(),
        ),
    )

    # Configure AssemblyAI STT with advanced turn detection
    # stt = AssemblyAISTTService(
    #     api_key=os.getenv("ASSEMBLYAI_API_KEY"),
    #     vad_force_turn_endpoint=False,
    #     connection_params=AssemblyAIConnectionParams(
    #         end_of_turn_confidence_threshold=0.7,
    #         min_end_of_turn_silence_when_confident=160,
    #         max_turn_silence=2400,
    #     )
    # )
    # stt = GroqSTTService(
    #     model="whisper-large-v3-turbo",
    #     api_key=os.getenv("GROQ_API_KEY"),
    #     language=Language.ZH,
    #     # prompt="Transcribe the following conversation",
    #     temperature=0.0
    # )
    stt = GladiaSTTService(api_key=os.getenv("GLADIA_API_KEY"),
        model="solaria-1",
        params=GladiaInputParams(
            language_config=LanguageConfig(
                languages=[Language.EN, Language.ZH, Language.JA],
                code_switching=True
            ),
        ))

    # tts = CartesiaTTSService(
    #     api_key=os.getenv("CARTESIA_API_KEY"),
    #     voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",  # British Reading Lady
    # )
    tts = ElevenLabsTTSService(api_key=os.getenv("ELEVENLABS_API_KEY"),
                               voice_id="bhJUNIXWQQ94l8eI2VUf")

    # session = aiohttp.ClientSession()
    # tts = MiniMaxHttpTTSService(api_key=os.getenv("MINIMAX_API_KEY"),group_id=os.getenv("MINIMAX_GROUP_ID"),
                                # model="speech-02-turbo",
                                # voice_id="Patient_Man",
                                # params=MiniMaxHttpTTSService.InputParams(
                                #     language=Language.ZH,
                                #     speed=1.1,         # Slightly faster speech
                                #     volume=1.2,        # Slightly louder
                                #     pitch=0,           # Default pitch
                                #     emotion="neutral"  # Neutral emotional tone
                                # ),
                                # aiohttp_session=session)

    llm = OpenRouterLLMService(api_key=os.getenv("OPENROUTER_API_KEY"),model="openai/gpt-4o-mini")

    context = OpenAILLMContext(
        [
            {
                "role": "user",
                "content": "Start by greeting the user warmly and introducing yourself.",
            }
        ],
    )
    context_aggregator = llm.create_context_aggregator(context)

    # RTVI events for Pipecat client UI
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    pipeline = Pipeline(
        [
            ws_transport.input(),
            stt,
            context_aggregator.user(),
            rtvi,
            llm,  # LLM
            tts,
            ws_transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        logger.info("Pipecat client ready.")
        await rtvi.set_bot_ready()
        # Kick off the conversation.
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @ws_transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Pipecat Client connected")

    @ws_transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Pipecat Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)
