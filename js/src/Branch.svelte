<script>
  import { onMount } from "svelte";

  export let path;
  export let getSubscription;
  export let openWindow;

  let data;
  let opened = {};

  onMount(() => {
    const subscription = getSubscription(path);
    data = subscription.getState();
    const update_data = d => {
      data = d;
    };
    subscription.on("update", update_data);
    return () => {
      subscription.removeListener("update", update_data);
    };
  });

  const expander = path => () => {
    opened[path] = !opened[path];
  };

  const spawn = path => () => {
    openWindow({
      type: "component",
      componentName: "tree",
      componentState: { path },
    });
  };

  const command = cmd => () => {
    openWindow({
      type: "component",
      componentName: "command",
      componentState: { path, cmd },
    });
  };
</script>

<style>
  div.row {
    padding: 3px;
  }

  div.objectContents {
    margin-left: 0.35em;
    border-left: 2px solid rgb(128, 128, 128);
    padding: 0px 0px 0px 20px;
  }

  span.expander {
    padding: 0px 1ex 0px 0px;
    cursor: default;
  }

  pre.itemValue {
    display: inline-block;
    vertical-align: top;
    margin: 0;
    padding: 0.25em;
    border-left: 2px solid rgb(128, 64, 10);
  }

  svg {
    height: 1em;
  }

  svg.cmd {
    fill: none;
    stroke: currentColor;
    stroke-width: 2px;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  svg.spawn {
    fill: currentColor;
    stroke: none;
  }
</style>

{#if data === undefined}
  fetching...
{:else}
  {#each data as item, idx (idx)}
    <div class="row">
      {#if item.command !== undefined}
        <svg class="cmd" viewBox="0 -4 24 28" on:click={command(item)}>
          <path
            d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0
            0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3
            3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z"
          />
        </svg>
        &#x2007;{item.command}{item.signature}
      {:else if item.value !== undefined}
        <tt>
          {#if item.key === undefined}
            {idx}
          {:else}{JSON.stringify(item.key)}{/if}
        </tt>
        :&#x2007;
        {#if typeof item.value === 'string' && item.value.indexOf('\n') >= 0}
          <pre class="itemValue">{item.value}</pre>
        {:else}
          <tt class="itemValue">{JSON.stringify(item.value)}</tt>
        {/if}
      {:else}
        <span class="expander" on:click={expander(item.path)}>
          {opened[item.path] ? '⊟' : '⊞'}
        </span>
        <tt>
          {#if item.key === undefined}
            {idx}
          {:else}{JSON.stringify(item.key)}{/if}
        </tt>
        :&#x2007;{item.symbols[0]} {item.items} item{item.items === 1 ? '' : 's'}
        <svg class="spawn" viewBox="0 -2 24 24" on:click={spawn(item.path)}>
          <path
            d="M19,19 L5,19 L5,5 L12,5 L12,3 L5,3 C3.89,3 3,3.9 3,5 L3,19
            C3,20.1 3.89,21 5,21 L19,21 C20.1,21 21,20.1 21,19 L21,12 L19,12
            L19,19 Z M14,3 L14,5 L17.59,5 L7.76,14.83 L9.17,16.24 L19,6.41
            L19,10 L21,10 L21,3 L14,3 Z"
          />
        </svg>
        {#if opened[item.path]}
          <div class="objectContents">
            <svelte:self path={item.path} {getSubscription} {openWindow} />
          </div>
          <div>{item.symbols[1]}</div>
        {:else}{item.symbols[1]}{/if}
      {/if}
    </div>
  {/each}
{/if}
