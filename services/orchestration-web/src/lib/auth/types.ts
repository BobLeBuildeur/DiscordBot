export interface LoginCredentials {
	email: string;
	password: string;
}

export type LoginResult =
	| { ok: true; accessToken: string; tokenType: string }
	| { ok: false; error: string };

export interface AuthAdapter {
	login(credentials: LoginCredentials): Promise<LoginResult>;
}
