<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { createHttpAuthAdapter, setAccessToken, isAccessTokenValid } from '$lib/auth/index.js';

	const auth = createHttpAuthAdapter();

	let email = $state('');
	let password = $state('');
	let error = $state<string | null>(null);
	let submitting = $state(false);

	const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	const passwordPattern = /^[a-zA-Z0-9]{8,}$/;

	$effect(() => {
		if (!browser) return;
		if (isAccessTokenValid()) {
			goto('/');
		}
	});

	async function onsubmit(e: Event) {
		e.preventDefault();
		error = null;
		const em = email.trim();
		if (!emailPattern.test(em)) {
			error = 'Enter a valid email address.';
			return;
		}
		if (!passwordPattern.test(password)) {
			error = 'Password must be at least 8 alphanumeric characters.';
			return;
		}
		submitting = true;
		try {
			const result = await auth.login({ email: em, password });
			if (!result.ok) {
				error = result.error;
				return;
			}
			setAccessToken(result.accessToken);
			goto('/');
		} finally {
			submitting = false;
		}
	}
</script>

<div class="wrap">
	<div class="card">
		<h1 class="title">Sign in</h1>
		<p class="hint">Use your analyst email and password.</p>

		<form class="form" onsubmit={onsubmit}>
			<label class="label">
				<span class="label-text">Email</span>
				<input
					class="input"
					type="email"
					autocomplete="username"
					bind:value={email}
					required
					disabled={submitting}
				/>
			</label>
			<label class="label">
				<span class="label-text">Password</span>
				<input
					class="input"
					type="password"
					autocomplete="current-password"
					bind:value={password}
					required
					disabled={submitting}
				/>
			</label>

			{#if error}
				<p class="err" role="alert">{error}</p>
			{/if}

			<button class="submit" type="submit" disabled={submitting}>
				{submitting ? 'Signing in…' : 'Sign in'}
			</button>
		</form>
	</div>
</div>

<style>
	.wrap {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-4);
	}

	.card {
		width: 100%;
		/* At most mobile-lg viewport width (see tokens.css / components.md Grid). */
		max-width: var(--breakpoint-mobile-lg);
		background: var(--bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-2);
		box-shadow: var(--shadow-2);
		padding: var(--spacing-5);
	}

	.title {
		margin: 0 0 var(--spacing-2);
		font-size: var(--font-size-5);
		font-weight: var(--font-weight-bold);
		color: var(--text-primary);
	}

	.hint {
		margin: 0 0 var(--spacing-4);
		font-size: var(--font-size-3);
		color: var(--text-secondary);
	}

	.form {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
	}

	.label {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.label-text {
		font-size: var(--font-size-2);
		font-weight: var(--font-weight-medium);
		color: var(--text-secondary);
	}

	.input {
		font: inherit;
		padding: var(--spacing-2) var(--spacing-3);
		border-radius: var(--radius-1);
		border: 1px solid var(--color-border);
		background: var(--bg-card);
		color: var(--text-primary);
	}

	.input:focus {
		outline: 2px solid color-mix(in srgb, var(--color-primary), transparent 40%);
		outline-offset: 1px;
	}

	.err {
		margin: 0;
		font-size: var(--font-size-2);
		color: var(--color-warning);
	}

	.submit {
		font: inherit;
		font-weight: var(--font-weight-medium);
		margin-top: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		border: none;
		border-radius: var(--radius-1);
		cursor: pointer;
		background: var(--color-primary);
		color: var(--color-surface);
	}

	.submit:disabled {
		opacity: 0.7;
		cursor: default;
	}
</style>
