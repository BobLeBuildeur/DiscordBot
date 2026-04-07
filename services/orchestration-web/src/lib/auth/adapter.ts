import { env } from '$env/dynamic/public';
import type { AuthAdapter, LoginCredentials, LoginResult } from './types.js';

function authBase(): string {
	return env.PUBLIC_AUTH_API_URL ?? '';
}

export function createHttpAuthAdapter(): AuthAdapter {
	return {
		async login(credentials: LoginCredentials): Promise<LoginResult> {
			const r = await fetch(`${authBase()}/auth/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					email: credentials.email,
					password: credentials.password
				})
			});

			if (r.status === 401) {
				return { ok: false, error: 'Invalid email or password.' };
			}
			if (r.status === 422) {
				return { ok: false, error: 'Invalid email or password format.' };
			}
			if (!r.ok) {
				const text = await r.text();
				return { ok: false, error: text || `Login failed (${r.status})` };
			}

			const data = (await r.json()) as { access_token?: string; token_type?: string };
			if (typeof data.access_token !== 'string') {
				return { ok: false, error: 'Unexpected login response.' };
			}
			return {
				ok: true,
				accessToken: data.access_token,
				tokenType: typeof data.token_type === 'string' ? data.token_type : 'bearer'
			};
		}
	};
}
