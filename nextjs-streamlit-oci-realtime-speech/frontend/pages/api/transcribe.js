const PYTHON_WS_URL = process.env.PYTHON_WS_URL || "ws://127.0.0.1:5000";

export const config = {
  api: {
    bodyParser: false, // We are processing multipart/form-data
  },
};

export default function handler(req, res) {
  const wsModule = require("ws");
  const WebSocketServer = wsModule.WebSocketServer;
  const WebSocket = wsModule.WebSocket;

  const closeClientSocket = (socket) => {
    if (!socket) return;
    try {
      if (
        socket.readyState === WebSocket.CLOSING ||
        socket.readyState === WebSocket.CLOSED
      ) {
        return;
      }
      socket.close();
    } catch (error) {
      console.warn("Ignoring client close error:", error);
    }
  };

  const closePythonSocket = (socket) => {
    if (!socket) return;
    try {
      if (socket.readyState === WebSocket.CLOSED) return;
      if (socket.readyState === WebSocket.CONNECTING) {
        socket.once("open", () => closePythonSocket(socket));
        return;
      }
      socket.close();
    } catch (error) {
      console.warn("Ignoring python close error:", error);
    }
  };

  const server = res.socket.server;

  if (!server.ws) {
    const wss = new WebSocketServer({ noServer: true });

    // Handle WebSocket connection
    wss.on("connection", function connection(ws) {
      console.log("New WebSocket connection established");

      // Forward audio data to Python backend
      const pythonWs = new WebSocket(PYTHON_WS_URL);

      pythonWs.on("open", () => {
        console.log("Connected to Python backend");
      });

      pythonWs.on("error", (error) => {
        console.error("Python backend websocket error:", error.message);
      });

      ws.on("error", (error) => {
        console.error("Client websocket error:", error.message);
      });

      pythonWs.on("message", (data) => {
        // Forward transcription results back to client
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(data);
        }
      });

      ws.on("message", (data, isBinary) => {
        try {
          if (!isBinary) {
            const text = Buffer.isBuffer(data) ? data.toString("utf8") : String(data);
            const message = JSON.parse(text);

            if (message.type === "ping") {
              ws.send(JSON.stringify({ type: "pong" }));
              return;
            }

            if (message.type === "close" && pythonWs.readyState === WebSocket.OPEN) {
              pythonWs.send(text);
              return;
            }
          }

          if (isBinary && pythonWs.readyState === WebSocket.OPEN) {
            pythonWs.send(data);
          }
        } catch (error) {
          console.error("Error processing WebSocket message:", error);
        }
      });

      ws.on("close", () => {
        console.log("Client disconnected");
        closePythonSocket(pythonWs);
      });

      pythonWs.on("close", () => {
        console.log("Python backend disconnected");
        closeClientSocket(ws);
      });
    });

    server.ws = wss;
  }

  if (!server.wsUpgradeAttached) {
    server.wsUpgradeAttached = true;
    server.on("upgrade", (request, socket, head) => {
      if (request.url !== "/api/transcribe") {
        return;
      }

      server.ws.handleUpgrade(request, socket, head, (ws) => {
        server.ws.emit("connection", ws, request);
      });
    });
  }

  res.end();
}
