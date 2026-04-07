<script lang="ts">
	import { page } from '$app/state';
	import History from '$lib/components/History.svelte';
	import MessageInput from '$lib/components/MessageInput.svelte';
	import { captureEvent } from '$lib/analytics/posthog.js';
	import { redactClientErrorMessage } from '$lib/analytics/fingerprint.js';
	import { getSession, sendMessage } from '$lib/api.js';
	import type { Message } from '$lib/types.js';

	function createMessage(
		role: Message['role'],
		body: string,
		kind = 'message',
		frozen = true
	): Message {
		const idPart =
			globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
		return {
			id: `${role}-${kind}-${idPart}`,
			role,
			body,
			kind,
			frozen,
			inline_feedback: []
		};
	}

	let sessionId = $derived(page.params.sessionId ?? '');

	let messages: Message[] = $state([]);
	let loading = $state(true);
	let loadError = $state<string | null>(null);
	let sending = $state(false);
	let streamingBody = $state('');
	let isStreaming = $state(false);
	let streamingAssistantKind = $state('message');
	const streamingMessageId = 'streaming-agent';

	// Debounce plan feedback analytics: rapid edits while composing should not flood PostHog.
	let planFeedbackDebounce: ReturnType<typeof setTimeout> | null = null;

	let displayMessages: Message[] = $derived(
		isStreaming
			? [
					...messages,
					{
						id: streamingMessageId,
						role: 'agent',
						body: streamingBody,
						kind: streamingAssistantKind,
						frozen: true,
						inline_feedback: []
					}
				]
			: messages
	);

	$effect(() => {
		const id = sessionId;
		if (!id) {
			loading = false;
			return;
		}

		let cancelled = false;

		(async () => {
			loading = true;
			loadError = null;
			messages = [];
			const loadStarted = performance.now();
			try {
				const loaded = await getSession(id);
				if (cancelled) return;
				messages = loaded;
				captureEvent('orchestration_session_loaded', {
					session_id: id,
					message_count: loaded.length,
					load_duration_ms: Math.round(performance.now() - loadStarted),
					error: false
				});
			} catch (err) {
				if (cancelled) return;
				messages = [];
				loadError =
					err instanceof Error ? err.message : 'Failed to load session';
				captureEvent('orchestration_session_loaded', {
					session_id: id,
					message_count: 0,
					load_duration_ms: Math.round(performance.now() - loadStarted),
					error: true
				});
			} finally {
				if (!cancelled) loading = false;
			}
		})();

		return () => {
			cancelled = true;
		};
	});

	async function handleSend(text: string) {
		sending = true;
		const latestPlanIndex = [...messages]
			.reverse()
			.findIndex((msg) => msg.role === 'agent' && msg.kind === 'plan' && !msg.frozen);
		const editablePlanIndex =
			latestPlanIndex >= 0 ? messages.length - 1 - latestPlanIndex : -1;
		const inlineFeedback =
			editablePlanIndex >= 0
				? messages[editablePlanIndex].inline_feedback
						.filter((item) => item.comment.trim().length > 0)
						.map((item) => ({
							quoted_text: item.quoted_text,
							comment: item.comment.trim()
						}))
				: [];

		if (editablePlanIndex >= 0) {
			messages = messages.map((msg, index) =>
				index === editablePlanIndex
					? {
							...msg,
							frozen: true,
							inline_feedback: msg.inline_feedback.map((item) => ({
								...item,
								state: 'reading'
							}))
						}
					: msg
			);
		}

		messages = [...messages, createMessage('analyst', text)];
		streamingBody = '';
		streamingAssistantKind = 'message';
		isStreaming = true;
		const streamStarted = performance.now();
		captureEvent('orchestration_message_sent', {
			session_id: sessionId,
			message_length: text.length,
			has_plan_inline_feedback: inlineFeedback.length > 0,
			inline_feedback_item_count: inlineFeedback.length
		});

		try {
			await sendMessage(sessionId, text, inlineFeedback, {
				onChunk(data) {
					streamingBody += data.content;
				},
				onFinal(data) {
					streamingBody = data.assistant_message;
					streamingAssistantKind = data.assistant_kind || 'message';
				}
			});

			isStreaming = false;
			captureEvent('orchestration_sse_stream_completed', {
				session_id: sessionId,
				flow: 'continue',
				assistant_kind: streamingAssistantKind,
				duration_ms: Math.round(performance.now() - streamStarted),
				http_status: 200
			});
			messages = [
				...messages,
				createMessage(
					'agent',
					streamingBody,
					streamingAssistantKind,
					streamingAssistantKind === 'plan' ? false : true
				)
			];
		} catch (err) {
			isStreaming = false;
			const msg = err instanceof Error ? err.message : 'Unknown error';
			captureEvent('orchestration_client_error', {
				session_id: sessionId,
				operation: 'send_message',
				error_message_redacted: redactClientErrorMessage(msg)
			});
			captureEvent('orchestration_sse_stream_completed', {
				session_id: sessionId,
				flow: 'continue',
				assistant_kind: streamingAssistantKind,
				duration_ms: Math.round(performance.now() - streamStarted),
				http_status: 0
			});
			console.error('Failed to send message:', err);
			messages = [
				...messages,
				createMessage('agent', `Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
			];
		} finally {
			sending = false;
		}
	}

	function handlePlanFeedbackChange(messageId: string, inlineFeedback: Message['inline_feedback']) {
		messages = messages.map((message) =>
			message.id === messageId ? { ...message, inline_feedback: inlineFeedback } : message
		);
		const count = inlineFeedback.filter((item) => item.comment.trim().length > 0).length;
		if (planFeedbackDebounce) clearTimeout(planFeedbackDebounce);
		planFeedbackDebounce = setTimeout(() => {
			captureEvent('plan_inline_feedback_changed', {
				session_id: sessionId,
				feedback_item_count: count
			});
		}, 800);
	}
</script>

<svelte:head>
	<title>Session</title>
</svelte:head>

<div class="page">
	<History
		messages={displayMessages}
		{loading}
		{loadError}
		onPlanFeedbackChange={handlePlanFeedbackChange}
	/>
	<MessageInput onSend={handleSend} disabled={sending || loading} />
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-height: 0;
	}
</style>
