export type Role = 'agent' | 'analyst';

export interface Message {
	role: Role;
	body: string;
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
