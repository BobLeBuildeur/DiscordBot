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
		padding: 0.45rem 0.6rem;
		background: #f7fafc;
		border-radius: 6px;
		box-shadow: 0 4px 14px rgba(15, 23, 42, 0.12);
		border: 1px solid #e2e8f0;
		border-left: 3px solid #4a90d9;
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
		border: 1px solid #cbd5e1;
		border-radius: 4px;
		padding: 0.35rem 0.5rem;
		font: inherit;
	}

	.feedback-input:focus {
		outline: none;
		border-color: #4a90d9;
		box-shadow: 0 0 0 2px rgba(74, 144, 217, 0.2);
	}

	.feedback-reading {
		margin: 0;
		color: #374151;
		white-space: pre-wrap;
	}
	.feedback-block[data-state='reading'] {
		background: #f8fafc;
		border-left-color: #94a3b8;
	}
</style>
