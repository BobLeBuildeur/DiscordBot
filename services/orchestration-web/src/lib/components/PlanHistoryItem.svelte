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

<style>
	.plan-history-item {
		padding: 0.75rem 1rem;
		border-radius: 6px;
		margin-bottom: 0.5rem;
		background-color: #f0f4f8;
		border-left: 3px solid #4a90d9;
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

	.selection-add {
		position: absolute;
		z-index: 15;
		transform: translateY(-100%);
		border: 1px solid #93c5fd;
		background: #eff6ff;
		color: #1d4ed8;
		border-radius: 999px;
		width: 1.7rem;
		height: 1.7rem;
		font-weight: 700;
		cursor: pointer;
	}

	.plan-body :global(.feedback-highlight) {
		background: #fde68a;
		padding: 0 0.05em;
		border-radius: 2px;
	}

	.plan-body :global(pre) {
		background: #1e1e2e;
		color: #cdd6f4;
		padding: 0.75rem 1rem;
		border-radius: 4px;
		overflow-x: auto;
		font-size: 0.875rem;
	}

	.plan-body :global(code) {
		font-size: 0.9em;
	}

	.plan-body :global(pre code) {
		background: none;
		padding: 0;
	}

	.plan-body :global(code:not(pre code)) {
		background: #e2e8f0;
		padding: 0.1em 0.35em;
		border-radius: 3px;
	}

	.plan-body :global(ul),
	.plan-body :global(ol) {
		padding-left: 1.5rem;
	}

	.plan-body :global(blockquote) {
		border-left: 3px solid #cbd5e1;
		margin-left: 0;
		padding-left: 1rem;
		color: #555;
	}

	.plan-body :global(table) {
		border-collapse: collapse;
		width: 100%;
		margin: 0.5rem 0;
	}

	.plan-body :global(th),
	.plan-body :global(td) {
		border: 1px solid #d1d5db;
		padding: 0.4rem 0.6rem;
		text-align: left;
	}

	.plan-body :global(th) {
		background: #e5e7eb;
		font-weight: 600;
	}
</style>
