<script lang="ts">
	import { goto } from '$app/navigation';
	import History from '$lib/components/History.svelte';
	import MessageInput from '$lib/components/MessageInput.svelte';
	import { startSession } from '$lib/api.js';
	import type { Message } from '$lib/types.js';

	let messages: Message[] = $state([]);
	let sending = $state(false);
	let streamingBody = $state('');
	let isStreaming = $state(false);

	let displayMessages: Message[] = $derived(
		isStreaming ? [...messages, { role: 'agent', body: streamingBody }] : messages
	);

	async function handleSend(text: string) {
		sending = true;
		messages = [{ role: 'analyst', body: text }];

		let sessionId = '';
		streamingBody = '';
		isStreaming = true;

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
				}
			});

			isStreaming = false;
			const finalMessages: Message[] = [
				{ role: 'analyst', body: text },
				{ role: 'agent', body: streamingBody }
			];
			messages = finalMessages;

			if (sessionId) {
				await goto(`/session/${sessionId}`, {
					state: { messages: finalMessages }
				});
			}
		} catch (err) {
			isStreaming = false;
			console.error('Failed to start session:', err);
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
		height: 100vh;
	}
</style>
