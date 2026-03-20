<script lang="ts">
	import type { Role } from '$lib/types.js';
	import { renderMarkdown } from '$lib/markdown.js';

	let { role, body }: { role: Role; body: string } = $props();

	let renderedHtml = $derived(role === 'agent' ? renderMarkdown(body) : '');
</script>

<div class="history-item" data-role={role}>
	<span class="role-label">{role === 'agent' ? 'Agent' : 'Analyst'}</span>
	{#if role === 'agent'}
		<div class="message-body agent-body">{@html renderedHtml}</div>
	{:else}
		<div class="message-body analyst-body">{body}</div>
	{/if}
</div>

<style>
	.history-item {
		padding: 0.75rem 1rem;
		border-radius: 6px;
		margin-bottom: 0.5rem;
	}

	.history-item[data-role='agent'] {
		background-color: #f0f4f8;
		border-left: 3px solid #4a90d9;
	}

	.history-item[data-role='analyst'] {
		background-color: #fdf6ec;
		border-left: 3px solid #d4a843;
	}

	.role-label {
		display: block;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		margin-bottom: 0.35rem;
		color: #666;
	}

	.message-body {
		line-height: 1.55;
	}

	.analyst-body {
		white-space: pre-wrap;
		word-break: break-word;
	}

	.agent-body :global(pre) {
		background: #1e1e2e;
		color: #cdd6f4;
		padding: 0.75rem 1rem;
		border-radius: 4px;
		overflow-x: auto;
		font-size: 0.875rem;
	}

	.agent-body :global(code) {
		font-size: 0.9em;
	}

	.agent-body :global(pre code) {
		background: none;
		padding: 0;
	}

	.agent-body :global(code:not(pre code)) {
		background: #e2e8f0;
		padding: 0.1em 0.35em;
		border-radius: 3px;
	}

	.agent-body :global(ul),
	.agent-body :global(ol) {
		padding-left: 1.5rem;
	}

	.agent-body :global(blockquote) {
		border-left: 3px solid #cbd5e1;
		margin-left: 0;
		padding-left: 1rem;
		color: #555;
	}

	.agent-body :global(table) {
		border-collapse: collapse;
		width: 100%;
		margin: 0.5rem 0;
	}

	.agent-body :global(th),
	.agent-body :global(td) {
		border: 1px solid #d1d5db;
		padding: 0.4rem 0.6rem;
		text-align: left;
	}

	.agent-body :global(th) {
		background: #e5e7eb;
		font-weight: 600;
	}
</style>
