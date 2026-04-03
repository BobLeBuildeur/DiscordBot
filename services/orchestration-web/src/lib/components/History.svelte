<script lang="ts">
	import type { Message } from '$lib/types.js';
	import HistoryItem from './HistoryItem.svelte';
	import PlanHistoryItem from './PlanHistoryItem.svelte';

	let {
		messages,
		loading = false,
		loadError = null,
		onPlanFeedbackChange
	}: {
		messages: Message[];
		loading?: boolean;
		loadError?: string | null;
		onPlanFeedbackChange?: (messageId: string, feedback: Message['inline_feedback']) => void;
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
	{#each messages as msg (msg.id)}
		{#if msg.role === 'agent' && msg.kind === 'plan'}
			<PlanHistoryItem
				messageId={msg.id}
				body={msg.body}
				frozen={msg.frozen}
				inlineFeedback={msg.inline_feedback}
				onFeedbackChange={onPlanFeedbackChange}
			/>
		{:else}
			<HistoryItem role={msg.role} body={msg.body} />
		{/if}
	{/each}
</div>

<style>
	/* Full-width grid; per-message width cap lives inside HistoryItem / PlanHistoryItem */
	.history {
		flex: 1;
		overflow-y: auto;
		display: grid;
		grid-template-columns: repeat(var(--layout-grid-columns), minmax(0, 1fr));
		gap: var(--layout-grid-gap);
		width: 100%;
		padding-block: var(--spacing-3);
		box-sizing: border-box;
		align-content: start;
	}

	.history > :global(*) {
		grid-column: 1 / -1;
	}

	.empty-hint {
		max-width: min(var(--layout-container-max-width), 100%);
		margin-inline: auto;
		padding-inline: var(--spacing-3);
		box-sizing: border-box;
		color: var(--text-secondary);
		text-align: center;
		margin-top: var(--spacing-4);
		font-style: italic;
	}

	.empty-hint.error {
		color: var(--color-warning);
	}
</style>
