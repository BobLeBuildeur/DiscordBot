<script lang="ts">
	import { tick } from 'svelte';
	import FeedbackBlock from './FeedbackBlock.svelte';
	import { renderMarkdown } from '$lib/markdown.js';
	import type { PlanInlineFeedback } from '$lib/types.js';

	const ANCHOR_GRID = 16;
	const STACK_STEP = 44;

	/**
	 * Business rule: feedback panels are absolutely positioned at an anchor (same idea as the “+”).
	 * Several comments can share one spot; if every panel used the same (left, top), they would fully
	 * overlap and only the top one would be usable. We must offset overlapping panels so each stays readable.
	 *
	 * Logic: (1) Read this item’s anchor in plan-root coordinates (defaults if missing).
	 * (2) Bucket anchors into a coarse grid (ANCHOR_GRID) so nearby pixels count as the same “spot.”
	 * (3) peers = all feedback in that grid cell. (4) index = this item’s order among peers.
	 * (5) Keep horizontal position at ax; add index * STACK_STEP to top so peers stack downward.
	 */
	function stackedOverlayPosition(
		item: PlanInlineFeedback,
		all: PlanInlineFeedback[]
	): { left: number; top: number } {
		const ax = item.anchor?.x ?? 8;
		const ay = item.anchor?.y ?? 8;
		const gx = Math.round(ax / ANCHOR_GRID);
		const gy = Math.round(ay / ANCHOR_GRID);
		const peers = all.filter((f) => {
			const fx = f.anchor?.x ?? 8;
			const fy = f.anchor?.y ?? 8;
			return Math.round(fx / ANCHOR_GRID) === gx && Math.round(fy / ANCHOR_GRID) === gy;
		});
		const index = peers.findIndex((f) => f.id === item.id);
		return { left: ax, top: ay + Math.max(0, index) * STACK_STEP };
	}

	let {
		messageId,
		body,
		frozen,
		inlineFeedback,
		onFeedbackChange
	}: {
		messageId: string;
		body: string;
		frozen: boolean;
		inlineFeedback: PlanInlineFeedback[];
		onFeedbackChange?: (messageId: string, feedback: PlanInlineFeedback[]) => void;
	} = $props();

	let planRoot: HTMLElement | undefined = $state();
	let selectedText = $state('');
	let showAddButton = $state(false);
	let addButtonPos = $state({ x: 0, y: 0 });

	const renderedHtml = $derived(renderMarkdown(body));
	const highlightedHtml = $derived(
		applyFeedbackHighlights(
			renderedHtml,
			inlineFeedback.filter((item) => item.state === 'editing' || item.state === 'reading')
		)
	);

	$effect(() => {
		if (typeof window === 'undefined') return;
		const onSelectionChange = () => handleSelectionChanged();
		document.addEventListener('selectionchange', onSelectionChange);
		return () => document.removeEventListener('selectionchange', onSelectionChange);
	});

	/** Hydrate `anchor` from highlighted `<mark>` when missing (e.g. server-loaded reading state). */
	$effect(() => {
		const items = inlineFeedback;
		const _html = highlightedHtml;
		if (typeof window === 'undefined' || !planRoot || items.length === 0) return;
		if (!items.some((item) => !item.anchor)) return;

		const escapeCssAttr =
			typeof CSS !== 'undefined' && typeof CSS.escape === 'function'
				? CSS.escape
				: (s: string) => s.replace(/\\/g, '\\\\').replace(/"/g, '\\"');

		let cancelled = false;
		void (async () => {
			await tick();
			await new Promise<void>((r) => requestAnimationFrame(() => r()));
			if (cancelled || !planRoot) return;

			const rootRect = planRoot.getBoundingClientRect();
			const next = items.map((item) => {
				if (item.anchor) return item;
				const mark = planRoot!.querySelector<HTMLElement>(
					`[data-feedback-highlight="${escapeCssAttr(item.id)}"]`
				);
				let x = 8;
				let y = 8;
				if (mark) {
					const rect = mark.getBoundingClientRect();
					x = rect.right - rootRect.left + 8;
					y = rect.top - rootRect.top - 8;
				}
				// Fallback: top-left inset when no mark (e.g. quote not found in rendered HTML).
				return { ...item, anchor: { x, y } };
			});

			const changed = next.some(
				(f, i) => JSON.stringify(f.anchor) !== JSON.stringify(items[i]?.anchor)
			);
			if (changed && !cancelled) updateFeedback(next);
		})();

		return () => {
			cancelled = true;
		};
	});

	function updateFeedback(next: PlanInlineFeedback[]) {
		onFeedbackChange?.(messageId, next);
	}

	function handleSelectionChanged() {
		if (frozen || !planRoot) {
			showAddButton = false;
			return;
		}
		const selection = window.getSelection();
		if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
			showAddButton = false;
			return;
		}
		const range = selection.getRangeAt(0);
		if (!planRoot.contains(range.commonAncestorContainer)) {
			showAddButton = false;
			return;
		}
		const quote = selection.toString().trim();
		if (!quote) {
			showAddButton = false;
			return;
		}
		selectedText = quote;
		const rangeRect = range.getBoundingClientRect();
		const rootRect = planRoot.getBoundingClientRect();
		addButtonPos = {
			x: rangeRect.right - rootRect.left + 8,
			y: rangeRect.top - rootRect.top - 8
		};
		showAddButton = true;
	}

	function addFeedbackFromSelection() {
		if (!selectedText) return;
		const next: PlanInlineFeedback[] = [
			...inlineFeedback,
			{
				id: `feedback-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
				quoted_text: selectedText,
				comment: '',
				state: 'editing',
				anchor: { x: addButtonPos.x, y: addButtonPos.y }
			}
		];
		updateFeedback(next);
		showAddButton = false;
		window.getSelection()?.removeAllRanges();
	}

	function handleFeedbackUpdate(updated: PlanInlineFeedback) {
		updateFeedback(inlineFeedback.map((item) => (item.id === updated.id ? updated : item)));
	}

	function handleFeedbackRemove(feedbackId: string) {
		updateFeedback(inlineFeedback.filter((item) => item.id !== feedbackId));
	}

	function applyFeedbackHighlights(markup: string, feedback: PlanInlineFeedback[]): string {
		if (typeof window === 'undefined' || feedback.length === 0) {
			return markup;
		}
		const container = window.document.createElement('div');
		container.innerHTML = markup;
		for (const item of feedback) {
			highlightFirstMatch(container, item.quoted_text, item.id);
		}
		return container.innerHTML;
	}

	function highlightFirstMatch(root: HTMLElement, quote: string, feedbackId: string) {
		const target = quote.trim();
		if (!target) return;
		const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
		let current = walker.nextNode();
		while (current) {
			const node = current as Text;
			const value = node.nodeValue ?? '';
			const idx = value.indexOf(target);
			if (
				idx >= 0 &&
				node.parentElement &&
				!node.parentElement.closest('[data-feedback-highlight]')
			) {
				const parent = node.parentNode;
				if (!parent) return;
				const before = value.slice(0, idx);
				const match = value.slice(idx, idx + target.length);
				const after = value.slice(idx + target.length);
				if (before) parent.insertBefore(document.createTextNode(before), node);
				const mark = document.createElement('mark');
				mark.className = 'feedback-highlight';
				mark.dataset.feedbackHighlight = feedbackId;
				mark.textContent = match;
				parent.insertBefore(mark, node);
				if (after) parent.insertBefore(document.createTextNode(after), node);
				parent.removeChild(node);
				return;
			}
			current = walker.nextNode();
		}
	}
</script>

<div class="plan-history-item" data-frozen={frozen}>
	<div class="plan-history-item__inner">
		<span class="role-label">Agent Plan</span>
		<div class="plan-body-wrap">
			<div
				class="plan-body"
				bind:this={planRoot}
				role="document"
				aria-label="Plan content"
			>
				{@html highlightedHtml}
				{#if !frozen && showAddButton}
					<button
						type="button"
						class="selection-add"
						style={`left:${addButtonPos.x}px; top:${addButtonPos.y}px;`}
						onclick={addFeedbackFromSelection}
						aria-label="Add feedback for selection"
					>
						+
					</button>
				{/if}
				{#each inlineFeedback as feedback (feedback.id)}
					{@const pos = stackedOverlayPosition(feedback, inlineFeedback)}
					<div
						class="feedback-float"
						style={`left:${pos.left}px; top:${pos.top}px;`}
						role="group"
						aria-label="Comment on selected plan text"
					>
						<FeedbackBlock
							{feedback}
							{frozen}
							onUpdate={handleFeedbackUpdate}
							onRemove={handleFeedbackRemove}
						/>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>

<style>
	/* card on inner; outer row is full width — see .cursor/design/components.md */
	.plan-history-item {
		width: 100%;
		margin-bottom: var(--spacing-1);
		box-sizing: border-box;
	}

	.plan-history-item__inner {
		max-width: min(var(--layout-container-max-width), 100%);
		margin-inline: auto;
		padding: var(--spacing-2) var(--spacing-3);
		border-radius: var(--radius-1);
		background-color: var(--bg-card);
		color: var(--text-primary);
		box-shadow: var(--shadow-1);
		box-sizing: border-box;
	}

	.role-label {
		display: block;
		font-size: var(--font-size-1);
		font-weight: var(--font-weight-bold);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		margin-bottom: var(--spacing-1);
		color: var(--text-secondary);
	}

	.plan-body-wrap {
		display: block;
	}

	.plan-body {
		line-height: 1.55;
		position: relative;
		word-break: break-word;
		overflow: visible;
	}

	.feedback-float {
		position: absolute;
		z-index: 20;
		transform: translateY(-100%);
		pointer-events: auto;
		min-width: 12rem;
		max-width: min(22rem, 92vw);
	}

	/* card + shadow.2 — see .cursor/design/components.md, tokens.md shadow.2 */
	.selection-add {
		position: absolute;
		z-index: 15;
		transform: translateY(-100%);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-1);
		border: 1px solid var(--color-border);
		background: var(--bg-card);
		color: var(--color-primary);
		border-radius: var(--radius-1);
		box-shadow: var(--shadow-2);
		width: 1.7rem;
		height: 1.7rem;
		font-weight: var(--font-weight-bold);
		cursor: pointer;
		line-height: 1;
	}

	.plan-body :global(.feedback-highlight) {
		background: color-mix(in srgb, var(--color-warning) 42%, var(--color-surface));
		padding: 0 0.05em;
		border-radius: var(--radius-1);
	}

	.plan-body :global(pre) {
		background: var(--color-text-primary);
		color: var(--color-surface);
		padding: var(--spacing-2) var(--spacing-3);
		border-radius: var(--radius-1);
		overflow-x: auto;
		font-size: var(--font-size-3);
	}

	.plan-body :global(code) {
		font-size: 0.9em;
	}

	.plan-body :global(pre code) {
		background: none;
		padding: 0;
	}

	.plan-body :global(code:not(pre code)) {
		background: color-mix(in srgb, var(--color-border) 55%, var(--color-surface));
		padding: 0.1em 0.35em;
		border-radius: var(--radius-1);
	}

	.plan-body :global(ul),
	.plan-body :global(ol) {
		padding-left: var(--spacing-4);
	}

	.plan-body :global(blockquote) {
		border-left: 3px solid var(--color-border);
		margin-left: 0;
		padding-left: var(--spacing-3);
		color: var(--text-secondary);
	}

	.plan-body :global(table) {
		border-collapse: collapse;
		width: 100%;
		margin: var(--spacing-1) 0;
	}

	.plan-body :global(th),
	.plan-body :global(td) {
		border: 1px solid var(--color-border);
		padding: var(--spacing-1) var(--spacing-2);
		text-align: left;
	}

	.plan-body :global(th) {
		background: var(--color-background);
		font-weight: var(--font-weight-bold);
	}
</style>
