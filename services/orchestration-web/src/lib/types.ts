export type Role = 'agent' | 'analyst';

export interface PlanInlineFeedback {
	id: string;
	quoted_text: string;
	comment: string;
	state: 'editing' | 'reading';
	/** Client-only overlay position relative to `.plan-body` (same convention as the floating "+"). */
	anchor?: { x: number; y: number };
}

export interface Message {
	id: string;
	role: Role;
	body: string;
	kind: string;
	frozen: boolean;
	inline_feedback: PlanInlineFeedback[];
}

export interface SessionEvent {
	session_id: string;
}

export interface ChunkEvent {
	content: string;
}

export interface FinalEvent {
	session_id: string;
	assistant_kind: string;
	assistant_message: string;
	state_check: Record<string, unknown>;
	response_metadata: Record<string, unknown>;
	current_plan_markdown: string | null;
}
