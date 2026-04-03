<script lang="ts">
	import '../lib/styles/tokens.css';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="" />
	<link
		href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"
		rel="stylesheet"
	/>
	<link rel="icon" href="/favicon.svg" />
</svelte:head>

{@render children()}

<style>
	:global(html, body) {
		margin: 0;
		padding: 0;
		font-family: var(--font-family);
		font-size: var(--font-size-3);
		font-weight: var(--font-weight-regular);
		line-height: var(--font-line-height);
		color: var(--text-primary);
		background: var(--bg-app);
	}

	:global(*, *::before, *::after) {
		box-sizing: border-box;
	}
</style>
