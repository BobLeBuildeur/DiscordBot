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
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		border-top: 1px solid #e0e0e0;
		background: #fafafa;
	}

	textarea {
		flex: 1;
		resize: vertical;
		padding: 0.5rem 0.75rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-family: inherit;
		font-size: 0.95rem;
		line-height: 1.4;
	}

	textarea:focus {
		outline: none;
		border-color: #4a90d9;
		box-shadow: 0 0 0 2px rgba(74, 144, 217, 0.2);
	}

	button {
		align-self: flex-end;
		padding: 0.5rem 1.25rem;
		background: #4a90d9;
		color: #fff;
		border: none;
		border-radius: 4px;
		font-size: 0.95rem;
		cursor: pointer;
	}

	button:hover:not(:disabled) {
		background: #3a7bc8;
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
