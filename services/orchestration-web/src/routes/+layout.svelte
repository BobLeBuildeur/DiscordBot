<script lang="ts">
	import '../lib/styles/tokens.css';
	import { browser } from '$app/environment';
	import { afterNavigate, goto } from '$app/navigation';
	import { page } from '$app/state';
	import { clearAccessToken, isAccessTokenValid } from '$lib/auth/token.js';
	import {
		acceptAnalyticsConsent,
		captureEvent,
		capturePageview,
		declineAnalyticsConsent,
		initPosthogBrowser,
		shouldShowConsentBanner
	} from '$lib/analytics/posthog.js';

	let { children } = $props();

	let showConsentBanner = $state(false);

	$effect(() => {
		if (!browser) return;
		initPosthogBrowser();
		showConsentBanner = shouldShowConsentBanner();
	});

	$effect(() => {
		if (!browser) return;
		const path = page.url.pathname;
		if (path === '/login') return;
		if (!isAccessTokenValid()) {
			goto('/login');
		}
	});

	afterNavigate(({ to }) => {
		if (!browser || !to) return;
		initPosthogBrowser();
		const path = to.url.pathname;
		captureEvent('app_boot', {
			route: path,
			has_valid_token: isAccessTokenValid()
		});
		if (path !== '/login') {
			capturePageview(to.url.href);
		}
	});

	let showBar = $derived(
		browser && page.url.pathname !== '/login' && isAccessTokenValid()
	);

	function logout() {
		captureEvent('logout_clicked');
		clearAccessToken();
		goto('/login');
	}

	function onConsentAccept() {
		acceptAnalyticsConsent();
		showConsentBanner = false;
		capturePageview(page.url.href);
	}

	function onConsentDecline() {
		declineAnalyticsConsent();
		showConsentBanner = false;
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
	{#if showConsentBanner}
		<div class="consent-backdrop" role="presentation"></div>
		<div class="consent-banner" role="dialog" aria-labelledby="consent-title">
			<p id="consent-title" class="consent-title">Analytics and cookies</p>
			<p class="consent-text">
				We use PostHog to understand product usage. No capture runs until you opt in. See your
				organization’s privacy notice for details.
			</p>
			<div class="consent-actions">
				<button type="button" class="consent-decline" onclick={onConsentDecline}>Decline</button>
				<button type="button" class="consent-accept" onclick={onConsentAccept}>Accept analytics</button>
			</div>
		</div>
	{/if}
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

	.consent-backdrop {
		position: fixed;
		inset: 0;
		background: color-mix(in srgb, var(--text-primary), transparent 70%);
		z-index: 1000;
	}

	.consent-banner {
		position: fixed;
		left: 50%;
		bottom: var(--spacing-4);
		transform: translateX(-50%);
		width: min(var(--layout-container-max-width), calc(100% - var(--spacing-6)));
		padding: var(--spacing-4);
		border-radius: var(--radius-2);
		border: 1px solid var(--color-border);
		background: var(--bg-card);
		box-shadow: var(--shadow-2);
		z-index: 1001;
	}

	.consent-title {
		margin: 0 0 var(--spacing-2);
		font-weight: var(--font-weight-bold);
		font-size: var(--font-size-4);
		color: var(--text-primary);
	}

	.consent-text {
		margin: 0 0 var(--spacing-3);
		font-size: var(--font-size-3);
		color: var(--text-secondary);
		line-height: var(--font-line-height);
	}

	.consent-actions {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-2);
		justify-content: flex-end;
	}

	.consent-decline,
	.consent-accept {
		font: inherit;
		font-size: var(--font-size-2);
		font-weight: var(--font-weight-medium);
		padding: var(--spacing-2) var(--spacing-3);
		border-radius: var(--radius-1);
		cursor: pointer;
	}

	.consent-decline {
		border: 1px solid var(--color-border);
		background: var(--bg-card);
		color: var(--text-primary);
	}

	.consent-accept {
		border: none;
		background: var(--color-primary);
		color: var(--color-surface);
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
