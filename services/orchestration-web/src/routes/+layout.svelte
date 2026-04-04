<script lang="ts">
	import '../lib/styles/tokens.css';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { clearAccessToken, isAccessTokenValid } from '$lib/auth/token.js';

	let { children } = $props();

	$effect(() => {
		if (!browser) return;
		const path = page.url.pathname;
		if (path === '/login') return;
		if (!isAccessTokenValid()) {
			goto('/login');
		}
	});

	let showBar = $derived(
		browser && page.url.pathname !== '/login' && isAccessTokenValid()
	);

	function logout() {
		clearAccessToken();
		goto('/login');
	}
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

<div class="shell">
	{#if showBar}
		<header class="bar">
			<span class="brand">Orchestration</span>
			<button type="button" class="logout" onclick={logout}>Log out</button>
		</header>
	{/if}
	<main class="main">
		{@render children()}
	</main>
</div>

<style>
	.shell {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	.bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-3) var(--spacing-4);
		border-bottom: 1px solid var(--color-border);
		background: var(--bg-card);
		box-shadow: var(--shadow-1);
	}

	.brand {
		font-weight: var(--font-weight-medium);
		color: var(--text-primary);
	}

	.logout {
		font: inherit;
		font-size: var(--font-size-2);
		padding: var(--spacing-1) var(--spacing-3);
		border-radius: var(--radius-1);
		border: 1px solid var(--color-border);
		background: var(--bg-card);
		color: var(--text-primary);
		cursor: pointer;
	}

	.logout:hover {
		background: color-mix(in srgb, var(--color-primary), transparent 88%);
	}

	.main {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-height: 0;
	}

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
