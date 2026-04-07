/** Non-crypto fingerprint for analytics (not security): problem text length + short hash. */

export async function problemStatementFingerprint(text: string): Promise<{
	problem_statement_length: number;
	problem_statement_hash: string;
}> {
	const trimmed = text.trim();
	const problem_statement_length = trimmed.length;
	const enc = new TextEncoder().encode(trimmed);
	const digest = await crypto.subtle.digest('SHA-256', enc);
	const bytes = new Uint8Array(digest);
	const problem_statement_hash = Array.from(bytes.slice(0, 8))
		.map((b) => b.toString(16).padStart(2, '0'))
		.join('');
	return { problem_statement_length, problem_statement_hash };
}

export function redactClientErrorMessage(message: string, maxLen = 120): string {
	const s = message.replace(/\s+/g, ' ').trim();
	return s.length <= maxLen ? s : `${s.slice(0, maxLen)}…`;
}
