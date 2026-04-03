import { PUBLIC_ORCHESTRATION_API_URL } from '$env/static/public';
import type {
	Message,
	SessionEvent,
	ChunkEvent,
	FinalEvent,
	PlanInlineFeedback
} from './types.js';

const BASE = PUBLIC_ORCHESTRATION_API_URL ?? '';

interface SSECallbacks {
	onSession?: (data: SessionEvent) => void;
	onChunk?: (data: ChunkEvent) => void;
	onFinal?: (data: FinalEvent) => void;
	onError?: (error: Error) => void;
}

async function streamSSE(url: string, body: Record<string, unknown>, callbacks: SSECallbacks): Promise<void> {
	const response = await fetch(url, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});

	if (!response.ok) {
		const text = await response.text();
		throw new Error(`API error ${response.status}: ${text}`);
	}

	const reader = response.body?.getReader();
	if (!reader) throw new Error('No response body');

	const decoder = new TextDecoder();
	let buffer = '';

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;

		buffer += decoder.decode(value, { stream: true });

		const events = parseSSEBuffer(buffer);
		buffer = events.remaining;

		for (const event of events.parsed) {
			if (event.type === 'session' && callbacks.onSession) {
				callbacks.onSession(JSON.parse(event.data));
			} else if (event.type === 'chunk' && callbacks.onChunk) {
				callbacks.onChunk(JSON.parse(event.data));
			} else if (event.type === 'final' && callbacks.onFinal) {
				callbacks.onFinal(JSON.parse(event.data));
			}
		}
	}
}

interface ParsedEvent {
	type: string;
	data: string;
}

interface ParseResult {
	parsed: ParsedEvent[];
	remaining: string;
}

function parseSSEBuffer(buffer: string): ParseResult {
	const parsed: ParsedEvent[] = [];
	const blocks = buffer.split('\n\n');
	const remaining = blocks.pop() ?? '';

	for (const block of blocks) {
		if (!block.trim()) continue;
		let eventType = '';
		let data = '';
		for (const line of block.split('\n')) {
			if (line.startsWith('event: ')) {
				eventType = line.slice(7).trim();
			} else if (line.startsWith('data: ')) {
				data = line.slice(6);
			}
		}
		if (eventType && data) {
			parsed.push({ type: eventType, data });
		}
	}

	return { parsed, remaining };
}

export async function startSession(
	problemStatement: string,
	callbacks: SSECallbacks
): Promise<void> {
	await streamSSE(`${BASE}/orchestrator/sessions`, { problem_statement: problemStatement }, callbacks);
}

export async function sendMessage(
	sessionId: string,
	message: string,
	planInlineFeedback: Array<{ quoted_text: string; comment: string }> = [],
	callbacks: SSECallbacks
): Promise<void> {
	await streamSSE(
		`${BASE}/orchestrator/sessions/${sessionId}/messages`,
		{ message, plan_inline_feedback: planInlineFeedback },
		callbacks
	);
}

function buildMessageId(index: number, role: string, kind: string): string {
	return `${index}-${role}-${kind}`;
}

/** Server payloads omit UI-only `anchor`; PlanHistoryItem derives it from highlight marks after paint. */
function toReadingFeedback(
	raw: Array<{ quoted_text: string; comment: string }>
): PlanInlineFeedback[] {
	return raw.map((item, idx) => ({
		id: `server-${idx}-${item.quoted_text.slice(0, 12)}`,
		quoted_text: item.quoted_text,
		comment: item.comment,
		state: 'reading'
	}));
}

function conversationHistoryToMessages(
	history: Array<{
		role: string;
		content: string;
		kind?: string;
		inline_feedback?: Array<{ quoted_text: string; comment: string }>;
	}>
): Message[] {
	const out: Message[] = [];
	let lastPlanIndex = -1;

	/** Once another message is appended, the prior plan (if any) is no longer the last message → frozen. */
	function freezePriorPlanIfPresent() {
		if (out.length < 2) return;
		const prior = out[out.length - 2];
		if (prior.role === 'agent' && prior.kind === 'plan') {
			prior.frozen = true;
		}
	}

	for (const turn of history) {
		const kind = typeof turn.kind === 'string' ? turn.kind : 'message';
		const id = buildMessageId(out.length, turn.role, kind);
		if (turn.role === 'user') {
			out.push({
				id,
				role: 'analyst',
				body: turn.content,
				kind,
				frozen: true,
				inline_feedback: []
			});
			freezePriorPlanIfPresent();
			if (
				lastPlanIndex >= 0 &&
				Array.isArray(turn.inline_feedback) &&
				turn.inline_feedback.length > 0
			) {
				out[lastPlanIndex].inline_feedback = toReadingFeedback(turn.inline_feedback);
			}
		} else if (turn.role === 'assistant') {
			const isPlan = kind === 'plan';
			out.push({
				id,
				role: 'agent',
				body: turn.content,
				kind,
				frozen: isPlan ? false : true,
				inline_feedback: []
			});
			freezePriorPlanIfPresent();
			if (isPlan) {
				lastPlanIndex = out.length - 1;
			}
		}
	}

	return out;
}

export async function getSession(sessionId: string): Promise<Message[]> {
	const response = await fetch(`${BASE}/orchestrator/sessions/${sessionId}`);
	if (!response.ok) {
		const text = await response.text();
		throw new Error(`API error ${response.status}: ${text}`);
	}
	const data = (await response.json()) as { conversation_history?: unknown };
	const raw = Array.isArray(data.conversation_history) ? data.conversation_history : [];
	const turns = raw.filter(
		(
			item
		): item is {
			role: string;
			content: string;
			kind?: string;
			inline_feedback?: Array<{ quoted_text: string; comment: string }>;
		} =>
			item !== null &&
			typeof item === 'object' &&
			'role' in item &&
			'content' in item &&
			typeof (item as { role: unknown }).role === 'string' &&
			typeof (item as { content: unknown }).content === 'string'
	);
	return conversationHistoryToMessages(turns);
}
