<script lang="ts">
	import type { Role } from '$lib/types.js';
	import { renderMarkdown } from '$lib/markdown.js';

	let { role, body }: { role: Role; body: string } = $props();

	let renderedHtml = $derived(role === 'agent' ? renderMarkdown(body) : '');
</script>

<div class="history-item" data-role={role}>
	<div class="history-item__inner">
		{#if role === 'agent'}
			<div class="message-body agent-body">{@html renderedHtml}</div>
		{:else}
			<div class="message-body analyst-body">{body}</div>
		{/if}
	</div>
</div>

<style>
	.history-item {
		width: 100%;
		margin-bottom: var(--spacing-1);
		box-sizing: border-box;
	}

	.history-item__inner {
		max-width: min(var(--layout-container-max-width), 100%);
		margin-inline: auto;
		padding: var(--spacing-2) var(--spacing-3);
		border-radius: var(--radius-1);
		box-sizing: border-box;
	}

	.history-item[data-role='analyst'] .history-item__inner {
		background-color: var(--bg-card);
		color: var(--text-primary);
		box-shadow: var(--shadow-1);
	}

	.message-body {
		line-height: 1.55;
	}

	.analyst-body {
		white-space: pre-wrap;
		word-break: break-word;
	}

	.agent-body :global(pre) {
		background: var(--color-text-primary);
		color: var(--color-surface);
		padding: var(--spacing-2) var(--spacing-3);
		border-radius: var(--radius-1);
		overflow-x: auto;
		font-size: var(--font-size-3);
	}

	.agent-body :global(code) {
		font-size: 0.9em;
	}

	.agent-body :global(pre code) {
		background: none;
		padding: 0;
	}

	.agent-body :global(code:not(pre code)) {
		background: color-mix(in srgb, var(--color-border) 55%, var(--color-surface));
		padding: 0.1em 0.35em;
		border-radius: var(--radius-1);
	}

	.agent-body :global(ul),
	.agent-body :global(ol) {
		padding-left: 1.5rem;
	}

	.agent-body :global(blockquote) {
		border-left: 3px solid var(--color-border);
		margin-left: 0;
		padding-left: var(--spacing-3);
		color: var(--text-secondary);
	}

	.agent-body :global(table) {
		border-collapse: collapse;
		width: 100%;
		margin: var(--spacing-1) 0;
	}

	.agent-body :global(th),
	.agent-body :global(td) {
		border: 1px solid var(--color-border);
		padding: var(--spacing-1) var(--spacing-2);
		text-align: left;
	}

	.agent-body :global(th) {
		background: var(--color-background);
		font-weight: var(--font-weight-bold);
	}
</style>
