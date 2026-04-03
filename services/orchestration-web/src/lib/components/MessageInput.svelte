<script lang="ts">
	let { onSend, disabled = false }: { onSend: (text: string) => void; disabled?: boolean } =
		$props();

	let draft = $state('');

	function handleSubmit() {
		const text = draft.trim();
		if (!text || disabled) return;
		draft = '';
		onSend(text);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			handleSubmit();
		}
	}
</script>

<form class="input-area" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
	<label for="message-input" class="sr-only">Message</label>
	<textarea
		id="message-input"
		bind:value={draft}
		onkeydown={handleKeydown}
		placeholder="Type your message…"
		rows={3}
		{disabled}
	></textarea>
	<button type="submit" disabled={disabled || !draft.trim()}>Send</button>
</form>

<style>
	.input-area {
		display: flex;
		gap: var(--spacing-1);
		padding: var(--spacing-2) var(--spacing-3);
		border-top: 1px solid var(--color-border);
		background: var(--color-background);
	}

	textarea {
		flex: 1;
		resize: vertical;
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-1);
		font-family: inherit;
		font-size: var(--font-size-3);
		line-height: var(--font-line-height);
	}

	textarea:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary) 25%, transparent);
	}

	button {
		align-self: flex-end;
		padding: var(--spacing-1) var(--spacing-4);
		background: var(--color-primary);
		color: var(--color-surface);
		border: none;
		border-radius: var(--radius-1);
		font-size: var(--font-size-3);
		cursor: pointer;
	}

	button:hover:not(:disabled) {
		background: color-mix(in srgb, var(--color-primary) 88%, black);
	}

	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border-width: 0;
	}
</style>
