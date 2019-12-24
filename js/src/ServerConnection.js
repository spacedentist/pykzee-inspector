import EventEmitter from "events";

// ============================================================================
export class Subscription extends EventEmitter {
  constructor(path, websocket_send) {
    super();
    this.state = undefined;

    this.on("newListener", (event, listener) => {
      if (event === "update" && this.listenerCount("update") === 0) {
        websocket_send({ subscribe: path });
      }
    });

    this.on("removeListener", (event, listener) => {
      if (event === "update" && this.listenerCount("update") === 0) {
        this.state = undefined;
        websocket_send({ unsubscribe: path });
      }
    });
  }

  update(state) {
    this.state = state;
    this.emit("update", state);
  }

  getState() {
    return this.state;
  }
}

// ============================================================================
export class ServerConnection extends EventEmitter {
  constructor(ws_url) {
    super();
    this.wsUrl = ws_url;
    this.subscriptions = {};
    this.webSocketConnected = false;
    this.webSocket = null;
    this.serial = 0;
    this.commandCallbacks = new Map();

    this.webSocketSend = this.webSocketSend.bind(this);
    this.wsOnMessage = this.wsOnMessage.bind(this);
    this.wsOnOpen = this.wsOnOpen.bind(this);
    this.wsOnClose = this.wsOnClose.bind(this);
  }

  connect() {
    this.disconnect();
    this.emit("connecting");
    const ws = (this.webSocket = new WebSocket(this.wsUrl));
    ws.onmessage = this.wsOnMessage;
    ws.onopen = this.wsOnOpen;
    ws.onerror = ws.onclose = this.wsOnClose;
  }

  disconnect() {
    const ws = this.webSocket;
    if (ws) {
      ws.onmessage = ws.onopen = ws.onerror = ws.onclose = null;
      try {
        ws.close();
      } catch (err) {
        console.warn(err);
      }
    }
    this.webSocketConnected = false;
    this.webSocket = null;

    for (const [key, o] of this.commandCallbacks) {
      o.reject(new Error("websocket connection closed"));
    }
    this.commandCallbacks = new Map();
  }

  sendCommand(path, command, args, kwargs) {
    const id = ++this.serial;
    const p = new Promise((resolve, reject) => {
      this.commandCallbacks.set(id, { resolve, reject });
    });
    this.webSocketSend({ path, command, args, kwargs, id });
    return p;
  }

  wsOnMessage(event) {
    console.log(`Received message (raw): ${event.data}`);
    const data = JSON.parse(event.data);
    console.log("Received message:", data);

    const id = data.id;
    if (id !== undefined) {
      const cb = this.commandCallbacks.get(id);
      if (cb !== undefined) {
        this.commandCallbacks.delete(id);
        cb.resolve(data);
      }
      return;
    }

    const sub = this.subscriptions[data.subscription];
    if (sub) {
      sub.update(data.state);
    }
  }

  wsOnOpen() {
    this.webSocketConnected = true;
    this.emit("open");

    for (const path in this.subscriptions) {
      const sub = this.subscriptions[path];
      if (sub && sub.listenerCount("update") > 0) {
        sub.update(undefined);
        this.webSocketSend({ subscribe: path });
      }
    }
  }

  wsOnClose(event) {
    if (event.type === "error") {
      this.emit("error");
    } else {
      this.emit("closed");
    }
    this.disconnect();
  }

  getSubscription(path) {
    let sub = this.subscriptions[path];
    if (!sub) {
      sub = this.subscriptions[path] = new Subscription(
        path,
        this.webSocketSend,
      );
    }
    return sub;
  }

  webSocketSend(msg) {
    if (this.webSocketConnected) {
      console.log("Sending message:", msg);
      this.webSocket.send(JSON.stringify(msg));
    }
  }
}
