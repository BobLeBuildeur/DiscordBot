<script lang="ts">
	import { page } from '$app/state';
	import History from '$lib/components/History.svelte';
	import MessageInput from '$lib/components/MessageInput.svelte';
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
			try {
				const loaded = await getSession(id);
				if (cancelled) return;
				messages = loaded;
			} catch (err) {
				if (cancelled) return;
				messages = [];
				loadError =
					err instanceof Error ? err.message : 'Failed to load session';
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
	}
</script>

<svelte:head>
	<title>Session — {sessionId}</title>
</svelte:head>

<div class="page">
	<header class="session-header">
		<span class="session-id">Session: {sessionId}</span>
	</header>
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
		height: 100vh;
	}

	.session-header {
		padding: 0.5rem 1rem;
		border-bottom: 1px solid #e0e0e0;
		background: #fafafa;
	}

	.session-id {
		font-size: 0.8rem;
		color: #888;
		font-family: monospace;
	}
</style>
