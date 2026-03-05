import { useState, useRef, useEffect } from "react";
import { useShallow } from "zustand/shallow";

import { useTranscriptionStore } from "../stores/transcriptionStore";

export default function Home() {
  const [copyStatus, setCopyStatus] = useState("Copy transcript");
  const {
    recording,
    setRecording,
    transcript,
    setTranscript,
    partialTranscript,
    setPartialTranscript,
    audioDevices,
    setAudioDevices,
    selectedDevice,
    setSelectedDevice,
    audioLevel,
    setAudioLevel,
    startupError,
    setStartupError,
    starting,
    setStarting,
    resetTranscripts,
  } = useTranscriptionStore(
    useShallow((state) => ({
      recording: state.recording,
      setRecording: state.setRecording,
      transcript: state.transcript,
      setTranscript: state.setTranscript,
      partialTranscript: state.partialTranscript,
      setPartialTranscript: state.setPartialTranscript,
      audioDevices: state.audioDevices,
      setAudioDevices: state.setAudioDevices,
      selectedDevice: state.selectedDevice,
      setSelectedDevice: state.setSelectedDevice,
      audioLevel: state.audioLevel,
      setAudioLevel: state.setAudioLevel,
      startupError: state.startupError,
      setStartupError: state.setStartupError,
      starting: state.starting,
      setStarting: state.setStarting,
      resetTranscripts: state.resetTranscripts,
    }))
  );

  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const sourceNodeRef = useRef(null);
  const workletNodeRef = useRef(null);
  const streamRef = useRef(null);
  const recordingRef = useRef(false);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    recordingRef.current = recording;
  }, [recording]);

  useEffect(() => {
    let active = true;

    const loadAudioDevices = async () => {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(
          (device) => device.kind === "audioinput"
        );

        if (!active) return;
        setAudioDevices(audioInputs);
        if (audioInputs.length > 0) {
          setSelectedDevice(audioInputs[0].deviceId);
        }
      } catch (error) {
        console.error("Error loading audio devices:", error);
      }
    };

    const handleDeviceChange = async () => {
      try {
        const updatedDevices = await navigator.mediaDevices.enumerateDevices();
        const updatedAudioInputs = updatedDevices.filter(
          (device) => device.kind === "audioinput"
        );
        if (!active) return;
        setAudioDevices(updatedAudioInputs);
      } catch (error) {
        console.error("Error refreshing audio devices:", error);
      }
    };

    loadAudioDevices();

    navigator.mediaDevices.addEventListener("devicechange", handleDeviceChange);

    return () => {
      active = false;
      navigator.mediaDevices.removeEventListener("devicechange", handleDeviceChange);
    };
  }, []);

  const ORACLE_AUDIO_CONFIG = {
    sampleRate: 16000,
    channels: 1,
    bufferSize: 2048,
    minAudioLevel: 0.005,
  };

  const scheduleReconnect = () => {
    if (!recordingRef.current) {
      return;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectTimeoutRef.current = null;
      if (recordingRef.current) {
        wsRef.current = connectWebSocket();
      }
    }, 3000);
  };

  const connectWebSocket = () => {
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const defaultBackendUrl = "127.0.0.1:5000";
    const backendUrl = process.env.NEXT_PUBLIC_PYTHON_WS_URL || `${wsProtocol}://${defaultBackendUrl}`;
    const ws = new WebSocket(backendUrl);

    ws.onopen = () => {
      console.log("WebSocket Connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        console.log("Received message:", {
          type: data.type || data.status,
          timestamp: new Date().toISOString(),
        });

        if (data.status === "success") {
          const latest = data.transcript || "";
          setTranscript(latest);
          setPartialTranscript("");
          return;
        }

        switch (data.type) {
          case "transcription":
            console.log("Transcription:", {
              text: data.text,
              isFinal: data.isFinal,
              confidence: data.confidence,
              timestamp: new Date().toISOString(),
            });

            // Update UI with transcription
            if (data.isFinal) {
              setTranscript((prev) => {
                const newTranscript = prev
                  ? `${prev}\n${data.text}`
                  : data.text;
                console.log("Updated final transcript:", newTranscript);
                return newTranscript;
              });
              setPartialTranscript("");
            } else {
              setPartialTranscript(data.text);
              console.log("Updated partial transcript:", data.text);
            }
            break;

          case "session_started":
            console.log("Session started:", {
              sessionId: data.sessionId,
              timestamp: new Date().toISOString(),
            });
            break;

          case "session_stopped":
            console.log("Session stopped:", {
              timestamp: new Date().toISOString(),
            });
            break;

          case "error":
            console.error("Error from server:", {
              message: data.message,
              timestamp: new Date().toISOString(),
            });
            break;

          case "connection_closed":
            console.log("Connection closed by server:", {
              code: data.code,
              message: data.message,
              timestamp: new Date().toISOString(),
            });
            cleanup();
            break;

          default:
            console.log("Unknown message type:", {
              type: data.type,
              data: data,
              timestamp: new Date().toISOString(),
            });
        }
      } catch (error) {
        console.error("Error processing message:", {
          error: error.message,
          rawData: event.data,
          timestamp: new Date().toISOString(),
        });
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket Error:", error);
      console.log("WebSocket state:", ws.readyState);
      scheduleReconnect();
    };

    ws.onclose = (event) => {
      console.log("WebSocket Disconnected:", {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean,
      });

      if (recordingRef.current) {
        console.log(
          "Connection closed while recording. Attempting to reconnect..."
        );
        scheduleReconnect();
      }

      cleanup();
    };

    return ws;
  };

  const cleanup = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }

    if (workletNodeRef.current) {
      workletNodeRef.current.port.onmessage = null;
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (wsRef.current) {
      try {
        if (
          wsRef.current.readyState === WebSocket.OPEN ||
          wsRef.current.readyState === WebSocket.CONNECTING
        ) {
          wsRef.current.close();
        }
      } catch (error) {
        console.error("Error closing websocket during cleanup:", error);
      }
      wsRef.current = null;
    }

    setRecording(false);
  };

  const handleStartRecording = async () => {
    if (starting || recordingRef.current) {
      return;
    }

    setStarting(true);
    setStartupError("");
    resetTranscripts();

    try {
      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            deviceId: selectedDevice ? { exact: selectedDevice } : undefined,
            sampleRate: ORACLE_AUDIO_CONFIG.sampleRate,
            channelCount: ORACLE_AUDIO_CONFIG.channels,
          },
        });
      } catch (error) {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: ORACLE_AUDIO_CONFIG.sampleRate,
            channelCount: ORACLE_AUDIO_CONFIG.channels,
          },
        });
      }

      streamRef.current = stream;

      const audioContext = new AudioContext({
        sampleRate: ORACLE_AUDIO_CONFIG.sampleRate,
      });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      sourceNodeRef.current = source;

      if (!audioContext.audioWorklet || typeof AudioWorkletNode === "undefined") {
        throw new Error("AudioWorklet is not supported in this browser");
      }

      await audioContext.audioWorklet.addModule("/audio-processor.js");
      const workletNode = new AudioWorkletNode(audioContext, "pcm-processor", {
        numberOfInputs: 1,
        numberOfOutputs: 0,
        channelCount: ORACLE_AUDIO_CONFIG.channels,
        processorOptions: {
          minAudioLevel: ORACLE_AUDIO_CONFIG.minAudioLevel,
        },
      });
      workletNodeRef.current = workletNode;

      workletNode.port.onmessage = (event) => {
        if (typeof event.data?.level === "number") {
          setAudioLevel(event.data.level);
        }

        if (
          event.data?.hasAudio &&
          event.data?.audioBuffer &&
          wsRef.current?.readyState === WebSocket.OPEN
        ) {
          wsRef.current.send(event.data.audioBuffer);
        }
      };

      source.connect(workletNode);

      wsRef.current = connectWebSocket();

      const connectionCheck = await new Promise((resolve) => {
        const ws = wsRef.current;
        if (!ws) {
          resolve({
            ok: false,
            message: "Backend websocket is not initialized.",
          });
          return;
        }

        if (ws.readyState === WebSocket.OPEN) {
          resolve({ ok: true });
          return;
        }

        const backendHint = `Backend is not connected at ${ws.url}. Start it with: uv run python server.py`;
        const timeout = setTimeout(() => {
          cleanupListeners();
          resolve({ ok: false, message: backendHint });
        }, 10000);

        const onOpen = () => {
          cleanupListeners();
          resolve({ ok: true });
        };

        const onError = () => {
          cleanupListeners();
          resolve({ ok: false, message: backendHint });
        };

        const onClose = () => {
          cleanupListeners();
          resolve({ ok: false, message: backendHint });
        };

        const cleanupListeners = () => {
          clearTimeout(timeout);
          ws.removeEventListener("open", onOpen);
          ws.removeEventListener("error", onError);
          ws.removeEventListener("close", onClose);
        };

        ws.addEventListener("open", onOpen);
        ws.addEventListener("error", onError);
        ws.addEventListener("close", onClose);
      });

      if (!connectionCheck.ok) {
        setStartupError(connectionCheck.message || "Backend is not connected.");
        cleanup();
        return;
      }

      setRecording(true);
    } catch (err) {
      console.error("Error starting recording:", err);
      setStartupError(err?.message || "Failed to start recording");
      cleanup();
    } finally {
      setStarting(false);
    }
  };

  const handleStopRecording = async () => {
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "close" }));
      }
    } catch (error) {
      console.error("Error in stop recording:", error);
    } finally {
      // Always perform cleanup
      cleanup();
    }
  };

  const handleCopyTranscript = async () => {
    if (!transcript) {
      return;
    }

    try {
      await navigator.clipboard.writeText(transcript);
      setCopyStatus("Copied!");
      setTimeout(() => setCopyStatus("Copy transcript"), 1500);
    } catch (error) {
      console.error("Failed to copy transcript:", error);
      setCopyStatus("Copy failed");
      setTimeout(() => setCopyStatus("Copy transcript"), 1500);
    }
  };

  const handleDownloadTranscript = () => {
    if (!transcript) {
      return;
    }

    const blob = new Blob([transcript], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "transcript.txt";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  // Cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold mb-6">Oracle AI Speech Recognition</h1>

      {startupError ? (
        <div className="mb-4 w-full max-w-2xl rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {startupError}
        </div>
      ) : null}

      {/* Microphone Selection */}
      <div className="mb-6 w-full max-w-2xl">
        <label
          htmlFor="microphone-select"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          Select Microphone
        </label>
        <select
          id="microphone-select"
          value={selectedDevice}
          onChange={(e) => setSelectedDevice(e.target.value)}
          className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          disabled={recording}
        >
          {audioDevices.map((device) => (
            <option key={device.deviceId} value={device.deviceId}>
              {device.label || `Microphone ${device.deviceId.slice(0, 5)}...`}
            </option>
          ))}
        </select>

        {/* Audio Level Meter */}
        {recording && (
          <div className="mt-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Audio Level:</span>
              <div className="flex-1 h-4 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-100"
                  style={{
                    width: `${Math.min(audioLevel * 1000, 100)}%`,
                    backgroundColor:
                      audioLevel > ORACLE_AUDIO_CONFIG.minAudioLevel
                        ? "#3B82F6" // blue-500
                        : "#EF4444", // red-500
                  }}
                />
              </div>
              <span className="text-sm text-gray-500 w-16">
                {(audioLevel * 100).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>
                Min: {(ORACLE_AUDIO_CONFIG.minAudioLevel * 100).toFixed(1)}%
              </span>
              <span>Current: {(audioLevel * 100).toFixed(1)}%</span>
              <span>Max: 100%</span>
            </div>
          </div>
        )}
      </div>

      {/* Recording Controls */}
      <div className="mb-6 flex items-center space-x-4">
        {!recording ? (
          <button
            onClick={handleStartRecording}
            disabled={!selectedDevice || starting}
            className={`${
              selectedDevice
                ? "bg-blue-500 hover:bg-blue-600"
                : "bg-gray-400 cursor-not-allowed"
            } text-white font-medium py-2 px-4 rounded flex items-center space-x-2`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z"
                clipRule="evenodd"
              />
            </svg>
            <span>{starting ? "Starting..." : "Start Recording"}</span>
          </button>
        ) : (
          <button
            onClick={handleStopRecording}
            className="bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-4 rounded flex items-center space-x-2"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 002 0V8a1 1 0 00-1-1zm4 0a1 1 0 00-1 1v4a1 1 0 002 0V8a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <span>Stop Recording</span>
          </button>
        )}
      </div>

      {/* Transcription Display */}
      <div className="w-full max-w-2xl bg-white shadow-lg rounded-lg p-6">
        <div className="mb-4">
          <h2 className="text-xl font-semibold mb-2">Live Transcript</h2>
          <p className="text-gray-600 italic">{partialTranscript}</p>
        </div>
        <div>
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-xl font-semibold">Final Transcript</h2>
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopyTranscript}
                disabled={!transcript}
                className={`rounded px-3 py-1.5 text-sm font-medium text-white ${
                  transcript
                    ? "bg-slate-700 hover:bg-slate-800"
                    : "bg-slate-400 cursor-not-allowed"
                }`}
              >
                {copyStatus}
              </button>
              <button
                onClick={handleDownloadTranscript}
                disabled={!transcript}
                className={`rounded px-3 py-1.5 text-sm font-medium text-white ${
                  transcript
                    ? "bg-emerald-600 hover:bg-emerald-700"
                    : "bg-emerald-300 cursor-not-allowed"
                }`}
              >
                Download transcript
              </button>
            </div>
          </div>
          <p className="whitespace-pre-wrap">
            {transcript || "No transcription yet..."}
          </p>
        </div>
      </div>
    </div>
  );
}
