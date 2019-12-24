<script>
  import Callout from "./Callout.svelte";

  const json_parse = x => {
    try {
      return JSON.parse(x);
    } catch (err) {}
  };

  export let path;
  export let cmd;
  export let sendCommand;
  let submitted = false;
  let result = undefined;
  let error = undefined;
  let tb;
  let args = "[]";
  $: args_parsed = json_parse(args);
  let kwargs = "{}";
  $: kwargs_parsed = json_parse(kwargs);

  const clearSubmitted = () => {
    submitted = false;
    result = undefined;
    error = undefined;
  };

  const submit = () => {
    submitted = true;

    sendCommand(path, cmd.command, args_parsed, kwargs_parsed).then(
      res => {
        if (res.error) {
          error = res.error;
          tb = res.tb;
        } else {
          result = res.result;
        }
      },
      err => {
        error = err.message;
      },
    );
  };
</script>

<style>
  .field {
    margin-bottom: 1em;
  }

  textarea {
    display: block;
    width: 100%;
    height: 4em;
  }
</style>

<h2>{cmd.command}{cmd.signature}</h2>

{#if result !== undefined}
  <Callout title="Command executed" calloutClass="info">
    <p>
      Result:
      <tt>{result}</tt>
    </p>
    <div>
      <button on:click={clearSubmitted}>Clear</button>
    </div>
  </Callout>
{/if}

{#if error !== undefined}
  <Callout title="Command execution failed" calloutClass="error">
    <p>{error}</p>
    {#if tb}
      <pre>{tb}</pre>
    {/if}
    <div>
      <button on:click={clearSubmitted}>Clear</button>
    </div>
  </Callout>
{/if}

<div class="field">
  <label for="args">Positional arguments [...]</label>
  <textarea id="args" bind:value={args} />
</div>

<div class="field">
  <label for="kwargs">Keyword arguments {'{...}'}</label>
  <textarea id="kwargs" bind:value={kwargs} />
</div>

<div>
  <button
    on:click={submit}
    disabled={submitted || args_parsed === undefined || kwargs_parsed === undefined}
  >
    Submit
  </button>
</div>
