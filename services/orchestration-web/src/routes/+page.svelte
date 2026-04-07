<script lang="ts">
	import { goto } from '$app/navigation';
	import History from '$lib/components/History.svelte';
	import MessageInput from '$lib/components/MessageInput.svelte';
	import { captureEvent } from '$lib/analytics/posthog.js';
	import { problemStatementFingerprint, redactClientErrorMessage } from '$lib/analytics/fingerprint.js';
	import { startSession } from '$lib/api.js';
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

	let messages: Message[] = $state([]);
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

	async function handleSend(text: string) {
		sending = true;
		messages = [createMessage('analyst', text)];

		let sessionId = '';
		streamingBody = '';
		streamingAssistantKind = 'message';
		isStreaming = true;
		const streamStarted = performance.now();
		const fp = await problemStatementFingerprint(text);
		captureEvent('orchestration_session_started', fp);

		try {
			await startSession(text, {
				onSession(data) {
					sessionId = data.session_id;
				},
				onChunk(data) {
					streamingBody += data.content;
				},
				onFinal(data) {
					streamingBody = data.assistant_message;
					sessionId = sessionId || data.session_id;
					streamingAssistantKind = data.assistant_kind || 'message';
				}
			});

			isStreaming = false;
			captureEvent('orchestration_sse_stream_completed', {
				session_id: sessionId,
				flow: 'start',
				assistant_kind: streamingAssistantKind,
				duration_ms: Math.round(performance.now() - streamStarted),
				http_status: 200
			});
			const finalMessages: Message[] = [
				createMessage('analyst', text),
				createMessage(
					'agent',
					streamingBody,
					streamingAssistantKind,
					streamingAssistantKind === 'plan' ? false : true
				)
			];
			messages = finalMessages;

			if (sessionId) {
				await goto(`/session/${sessionId}`, {
					state: { messages: finalMessages }
				});
			}
		} catch (err) {
			isStreaming = false;
			const msg = err instanceof Error ? err.message : 'Unknown error';
			captureEvent('orchestration_client_error', {
				session_id: sessionId || undefined,
				operation: 'start_session',
				error_message_redacted: redactClientErrorMessage(msg)
			});
			captureEvent('orchestration_sse_stream_completed', {
				session_id: sessionId,
				flow: 'start',
				assistant_kind: streamingAssistantKind,
				duration_ms: Math.round(performance.now() - streamStarted),
				http_status: 0
			});
			console.error('Failed to start session:', err);
			messages = [
				...messages,
				{
					...createMessage(
						'agent',
						`Error: ${err instanceof Error ? err.message : 'Unknown error'}`
					)
				}
			];
		} finally {
			sending = false;
		}
	}
</script>

<svelte:head>
	<title>Orchestration — New Session</title>
</svelte:head>

<div class="page">
	<History messages={displayMessages} />
	<MessageInput onSend={handleSend} disabled={sending} />
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-height: 0;
	}
</style>
