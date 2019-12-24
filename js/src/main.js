import GoldenLayout from "golden-layout";
import "golden-layout/src/css/goldenlayout-base.css";
import "golden-layout/src/css/goldenlayout-light-theme.css";
import "./style.css";

import { ServerConnection } from "./ServerConnection.js";
import Branch from "./Branch.svelte";
import Command from "./Command.svelte";

async function main() {
  const ws_url = (base => {
    const u = new URL("state", base);
    u.protocol = u.protocol.replace("http", "ws");
    return u.href;
  })(document.location);

  const server_connection = new ServerConnection(ws_url);
  const get_subscription = server_connection.getSubscription.bind(
    server_connection,
  );
  const send_command = server_connection.sendCommand.bind(server_connection);

  const gl_config = {
    content: [
      {
        type: "row",
        content: [
          {
            type: "component",
            componentName: "tree",
            componentState: { path: "/" },
          },
        ],
      },
    ],
  };
  const layout = new GoldenLayout(
    gl_config,
    window.document.getElementById("golden-layout"),
  );

  class TreeComponent {
    constructor(container, state) {
      const item = container.parent;

      const div1 = document.createElement("div");
      div1.className = "window1";
      container.getElement()[0].appendChild(div1);
      const div2 = document.createElement("div");
      div2.className = "window2";
      div1.appendChild(div2);

      container.setTitle(state.path);
      const tree = new Branch({
        target: div2,
        props: {
          path: state.path,
          getSubscription: get_subscription,
          openWindow: config => item.parent.addChild(config),
        },
      });

      container.on("destroy", () => tree.$destroy());
    }
  }
  layout.registerComponent("tree", TreeComponent);

  class CommandComponent {
    constructor(container, state) {
      const div1 = document.createElement("div");
      div1.className = "window1";
      container.getElement()[0].appendChild(div1);
      const div2 = document.createElement("div");
      div2.className = "window2";
      div1.appendChild(div2);

      container.setTitle(
        `${state.cmd.command}${state.cmd.signature} @ ${state.path}`,
      );
      const tree = new Command({
        target: div2,
        props: {
          path: state.path,
          cmd: state.cmd,
          sendCommand: send_command,
        },
      });

      container.on("destroy", () => tree.$destroy());
    }
  }
  layout.registerComponent("command", CommandComponent);

  layout.init();

  const portal = document.getElementById("connection-modal");
  const dialog_header = document.getElementById("dialog-header");
  const dialog_button = document.getElementById("button");
  server_connection.on("open", () => {
    portal.className = "off";
    dialog_header.innerHTML = "Connected";
    dialog_button.disabled = true;
  });
  server_connection.on("error", () => {
    portal.className = "on";
    dialog_header.innerHTML = "Connection error";
    dialog_button.disabled = false;
  });
  server_connection.on("closed", () => {
    portal.className = "on";
    dialog_header.innerHTML = "Connection closed";
    dialog_button.disabled = false;
  });
  server_connection.on("connecting", () => {
    portal.className = "on";
    dialog_header.innerHTML = "Connecting...";
    dialog_button.disabled = true;
  });
  dialog_button.onclick = () => server_connection.connect();

  server_connection.connect();
}

window.onload = () => {
  main().then(res => null, console.error);
};
