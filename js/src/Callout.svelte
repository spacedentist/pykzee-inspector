<script>
  export let title;
  export let calloutClass;
</script>

<style>
  div.outer {
    border: 2px solid black;
    border-radius: 0.5em;
    margin-bottom: 1em;
  }

  div.outer.info {
    border-color: #4f7fbf;
  }
  div.outer.error {
    border-color: #cf1f1f;
  }

  h2 {
    font-size: 1.5em;
    margin: 0;
    padding: 0.25em 1em;
    color: white;
  }

  div.outer.info h2 {
    background-color: #4f7fbf;
  }

  div.outer.error h2 {
    background-color: #cf1f1f;
  }

  div.inner {
    padding: 0.25em 1.5em;
  }
</style>

<div class={calloutClass} class:outer={true}>
  <h2>{title}</h2>
  <div class="inner">
    <slot />
  </div>
</div>
