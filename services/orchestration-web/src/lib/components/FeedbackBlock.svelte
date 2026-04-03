<script lang="ts">
	import type { PlanInlineFeedback } from '$lib/types.js';

	let {
		feedback,
		frozen,
		onUpdate,
		onRemove
	}: {
		feedback: PlanInlineFeedback;
		frozen: boolean;
		onUpdate: (feedback: PlanInlineFeedback) => void;
		onRemove: (feedbackId: string) => void;
	} = $props();

	let textareaEl: HTMLTextAreaElement | undefined = $state();
	let initialChromeDone = $state(false);

	let isReading = $derived(frozen || feedback.state === 'reading');
	let isEditing = $derived(!isReading);

	/** One-shot: size + focus for new editing rows; do not steal focus after blur. */
	$effect(() => {
		if (!isEditing || !textareaEl || initialChromeDone) return;
		requestAnimationFrame(() => {
			if (!textareaEl) return;
			textareaEl.style.height = 'auto';
			textareaEl.style.height = `${textareaEl.scrollHeight}px`;
			textareaEl.focus();
			textareaEl.setSelectionRange(textareaEl.value.length, textareaEl.value.length);
			initialChromeDone = true;
		});
	});

	function handleInput(event: Event) {
		const target = event.currentTarget as HTMLTextAreaElement;
		target.style.height = 'auto';
		target.style.height = `${target.scrollHeight}px`;
		onUpdate({
			...feedback,
			comment: target.value
		});
	}

	function handleBlur() {
		const trimmed = feedback.comment.trim();
		if (!trimmed) {
			onRemove(feedback.id);
		}
	}
</script>

<div
	class="feedback-block"
	data-state={isReading ? 'reading' : 'editing'}
	aria-label="Plan comment"
>
	{#if isReading}
		<p class="feedback-reading">{feedback.comment}</p>
	{:else}
		<textarea
			class="feedback-input"
			rows={1}
			bind:this={textareaEl}
			value={feedback.comment}
			oninput={handleInput}
			onblur={handleBlur}
			placeholder="Add feedback..."
			aria-label="Comment on selected plan text"
		></textarea>
	{/if}
</div>

<style>
	.feedback-block {
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-surface);
		border-radius: var(--radius-1);
		box-shadow: var(--shadow-1), 0 4px 14px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
		width: 100%;
		box-sizing: border-box;
	}

	.feedback-input {
		display: block;
		width: 100%;
		box-sizing: border-box;
		resize: none;
		overflow: hidden;
		line-height: 1.35;
		border: none;
		border-radius: var(--radius-1);
		padding: var(--spacing-1);
		font: inherit;
		background: var(--color-background);
	}

	.feedback-input:focus {
		outline: none;
		box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary) 25%, transparent);
	}

	.feedback-reading {
		margin: 0;
		color: var(--text-primary);
		white-space: pre-wrap;
	}
	.feedback-block[data-state='reading'] {
		background: color-mix(in srgb, var(--color-text-secondary) 6%, var(--color-surface));
	}
</style>
