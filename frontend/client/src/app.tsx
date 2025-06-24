import React, { useRef, useState, useEffect } from 'react';
import {
  RTVIClient,
  RTVIClientOptions,
  RTVIEvent,
} from '@pipecat-ai/client-js';
import { WebSocketTransport } from '@pipecat-ai/websocket-transport';
import { createRoot } from 'react-dom/client';
import { FiMic } from 'react-icons/fi';

interface ChatBubble {
  sender: 'user' | 'bot';
  text: string;
  time: string;
}

const App: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const [chat, setChat] = useState<ChatBubble[]>([]);
  const [debugLog, setDebugLog] = useState<string[]>([]);
  const botAudioRef = useRef<HTMLAudioElement>(null);
  const rtviClientRef = useRef<RTVIClient | null>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // 时间格式化
  const nowTime = () => new Date().toLocaleTimeString();

  // 日志
  const log = (msg: string) => {
    setDebugLog((prev) => [...prev, `${new Date().toISOString()} - ${msg}`]);
    // 控制台也输出
    console.log(msg);
  };

  // 拼接多段回复到同一个气泡
  const appendToBubble = (sender: 'user' | 'bot', text: string) => {
    setChat((prev) => {
      if (prev.length > 0 && prev[prev.length - 1].sender === sender) {
        // 拼接到最后一个气泡
        const last = prev[prev.length - 1];
        return [
          ...prev.slice(0, -1),
          { ...last, text: last.text + text, time: nowTime() },
        ];
      } else {
        // 新建气泡
        return [...prev, { sender, text, time: nowTime() }];
      }
    });
  };

  // 状态更新
  useEffect(() => {
    setIsConnected(status === 'connected');
  }, [status]);

  // 聊天自动滚动到底部
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chat]);

  // 连接
  const connect = async () => {
    setStatus('connecting');
    try {
      const transport = new WebSocketTransport();
      const RTVIConfig: RTVIClientOptions = {
        transport,
        params: {
          baseUrl: '',
          endpoints: { connect: '/connect' },
        },
        enableMic: true,
        enableCam: false,
        callbacks: {
          onConnected: () => setStatus('connected'),
          onDisconnected: () => {
            setStatus('disconnected');
            log('Client disconnected');
          },
          onBotReady: (data) => {
            // 不显示"AI已准备好"
            if (data && typeof data === 'object' && 'text' in data && (data as any).text) {
              appendToBubble('bot', (data as any).text);
            }
            setupMediaTracks();
          },
          onUserTranscript: (data) => {
            if (data.final) appendToBubble('user', data.text);
          },
          onBotTranscript: (data) => appendToBubble('bot', data.text),
          onMessageError: (error) => log('Message error: ' + error),
          onError: (error) => log('Error: ' + error),
        },
      };
      const client = new RTVIClient(RTVIConfig);
      rtviClientRef.current = client;
      setupTrackListeners(client);
      log('Initializing devices...');
      await client.initDevices();
      log('Connecting to bot...');
      await client.connect();
      log('Connection complete');
    } catch (e: any) {
      log('Error connecting: ' + e.message);
      setStatus('disconnected');
      if (rtviClientRef.current) {
        try { await rtviClientRef.current.disconnect(); } catch {}
      }
    }
  };

  // 断开
  const disconnect = async () => {
    if (rtviClientRef.current) {
      try {
        await rtviClientRef.current.disconnect();
        rtviClientRef.current = null;
        if (botAudioRef.current && botAudioRef.current.srcObject) {
          (botAudioRef.current.srcObject as MediaStream).getAudioTracks().forEach(track => track.stop());
          botAudioRef.current.srcObject = null;
        }
      } catch (e: any) {
        log('Error disconnecting: ' + e.message);
      }
    }
  };

  // 音频轨道
  const setupAudioTrack = (track: MediaStreamTrack) => {
    log('Setting up audio track');
    if (botAudioRef.current) {
      if (botAudioRef.current.srcObject && 'getAudioTracks' in botAudioRef.current.srcObject) {
        const oldTrack = (botAudioRef.current.srcObject as MediaStream).getAudioTracks()[0];
        if (oldTrack?.id === track.id) return;
      }
      botAudioRef.current.srcObject = new MediaStream([track]);
    }
  };

  // 检查媒体轨道
  const setupMediaTracks = () => {
    const client = rtviClientRef.current;
    if (!client) return;
    const tracks = client.tracks();
    if (tracks.bot?.audio) setupAudioTrack(tracks.bot.audio);
  };

  // 监听轨道事件
  const setupTrackListeners = (client: RTVIClient) => {
    client.on(RTVIEvent.TrackStarted, (track, participant) => {
      if (!participant?.local && track.kind === 'audio') setupAudioTrack(track);
    });
    client.on(RTVIEvent.TrackStopped, (track, participant) => {
      log(`Track stopped: ${track.kind} from ${participant?.name || 'unknown'}`);
    });
  };

  // 按钮点击
  const handleConnectClick = () => {
    if (isConnected) disconnect();
    else connect();
  };

  // 状态文本
  const statusText = {
    disconnected: '未连接',
    connecting: '连接中',
    connected: '已连接',
  }[status];

  // 按钮文本
  const btnText = {
    disconnected: 'Talk to AI Agent',
    connecting: 'Connecting...',
    connected: 'Stop',
  }[status];

  return (
    <div id="app-root">
      <div className="chat-header">
        <button
          id="connect-btn"
          className={`chat-btn ${status}`}
          onClick={handleConnectClick}
          disabled={status === 'connecting'}
        >
          {btnText}
          <span style={{marginLeft: 10, display: 'inline-flex', verticalAlign: 'middle'}}>
            <FiMic size={20} color="#222" />
          </span>
        </button>
      </div>
      {/* <div className="chat-desc">你好！这是一个AI语音助手，支持流式语音识别与对话。</div> */}
      <div id="chat-container" ref={chatContainerRef} style={{overflowY: 'auto', maxHeight: '60vh'}}>
        {chat.length === 0 ? (
          <div style={{textAlign: 'center', color: '#bbb', fontSize: '1.1rem', marginTop: '120px'}}>
            点击上方按钮开始对话
          </div>
        ) : (
          chat.map((bubble, idx) => (
            <div className="chat-bubble" key={idx}>
              <div className={`bubble-label ${bubble.sender === 'user' ? 'user' : 'ai'}`}>
                {bubble.sender === 'user' ? 'You' : 'AIGENT'}
              </div>
              <div className={bubble.sender === 'user' ? 'user-msg' : 'ai-msg'}>{bubble.text}</div>
              <div className="bubble-time">{bubble.time}</div>
            </div>
          ))
        )}
      </div>
      <div id="debug-log" style={{ display: 'none' }}>
        {debugLog.map((entry, idx) => <div key={idx}>{entry}</div>)}
      </div>
      <audio id="bot-audio" ref={botAudioRef} autoPlay />
    </div>
  );
};

if (typeof window !== 'undefined') {
  const rootEl = document.getElementById('app-root');
  if (rootEl) {
    createRoot(rootEl).render(<App />);
  }
}

export default App; 