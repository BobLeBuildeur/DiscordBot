<script lang="ts">
	import { page } from '$app/state';
	import History from '$lib/components/History.svelte';
	import MessageInput from '$lib/components/MessageInput.svelte';
	import { sendMessage } from '$lib/api.js';
	import type { Message } from '$lib/types.js';

	let sessionId = $derived(page.params.sessionId ?? '');

	let messages: Message[] = $state(restoreMessages());
	let sending = $state(false);
	let streamingBody = $state('');
	let isStreaming = $state(false);

	let displayMessages: Message[] = $derived(
		isStreaming ? [...messages, { role: 'agent', body: streamingBody }] : messages
	);

	function restoreMessages(): Message[] {
		if (typeof window !== 'undefined' && window.history.state?.messages) {
			return window.history.state.messages;
		}
		return [];
	}

	async function handleSend(text: string) {
		sending = true;
		messages = [...messages, { role: 'analyst', body: text }];
		streamingBody = '';
		isStreaming = true;

		try {
			await sendMessage(sessionId, text, {
				onChunk(data) {
					streamingBody += data.content;
				},
				onFinal(data) {
					streamingBody = data.assistant_message;
				}
			});

			isStreaming = false;
			messages = [...messages, { role: 'agent', body: streamingBody }];
		} catch (err) {
			isStreaming = false;
			console.error('Failed to send message:', err);
			messages = [
				...messages,
				{
					role: 'agent',
					body: `Error: ${err instanceof Error ? err.message : 'Unknown error'}`
				}
			];
		} finally {
			sending = false;
		}
	}
</script>

<svelte:head>
	<title>Session — {sessionId}</title>
</svelte:head>

<div class="page">
	<header class="session-header">
		<span class="session-id">Session: {sessionId}</span>
	</header>
	<History messages={displayMessages} />
	<MessageInput onSend={handleSend} disabled={sending} />
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
