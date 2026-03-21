<script lang="ts">
	import type { Message } from '$lib/types.js';
	import HistoryItem from './HistoryItem.svelte';

	let {
		messages,
		loading = false,
		loadError = null
	}: {
		messages: Message[];
		loading?: boolean;
		loadError?: string | null;
	} = $props();

	let container: HTMLElement | undefined = $state();

	$effect(() => {
		if (messages.length && container) {
			scrollToBottom();
		}
	});

	function scrollToBottom() {
		requestAnimationFrame(() => {
			if (container) {
				container.scrollTop = container.scrollHeight;
			}
		});
	}
</script>

<div class="history" bind:this={container}>
	{#if loading}
		<p class="empty-hint">Loading session…</p>
	{:else if loadError}
		<p class="empty-hint error">{loadError}</p>
	{:else if messages.length === 0}
		<p class="empty-hint">Describe your problem to begin a new session.</p>
	{/if}
	{#each messages as msg (msg)}
		<HistoryItem role={msg.role} body={msg.body} />
	{/each}
</div>

<style>
	.history {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
	}

	.empty-hint {
		color: #888;
		text-align: center;
		margin-top: 2rem;
		font-style: italic;
	}

	.empty-hint.error {
		color: #b00020;
	}
</style>
