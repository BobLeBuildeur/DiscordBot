import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';
import posthog from 'posthog-js';
import { CONSENT_VERSION, readStoredConsent, writeStoredConsent } from './consent.js';

const DISTINCT_KEY = 'orch_analytics_distinct_id';

let initialized = false;

function posthogKey(): string {
	return (env.PUBLIC_POSTHOG_KEY ?? '').trim();
}

function apiHost(): string | undefined {
	const h = (env.PUBLIC_POSTHOG_HOST ?? '').trim();
	return h.length > 0 ? h : undefined;
}

/** One-time browser init: default opt-out; re-apply stored consent without sending events for declines. */
export function initPosthogBrowser(): void {
	if (!browser || initialized) return;
	const key = posthogKey();
	if (!key) return;

	posthog.init(key, {
		api_host: apiHost(),
		opt_out_capturing_by_default: true,
		persistence: 'memory',
		autocapture: false,
		capture_pageview: false,
		capture_pageleave: false
	});
	initialized = true;

	const stored = readStoredConsent();
	if (stored === 'accepted') {
		posthog.opt_in_capturing();
		_identifyDistinctFromStorage();
	} else if (stored === 'declined') {
		posthog.opt_out_capturing();
	}
}

function _identifyDistinctFromStorage(): void {
	if (!browser) return;
	try {
		let id = localStorage.getItem(DISTINCT_KEY);
		if (!id) {
			id = crypto.randomUUID();
			localStorage.setItem(DISTINCT_KEY, id);
		}
		posthog.identify(id);
	} catch {
		/* private mode */
	}
}

export function shouldShowConsentBanner(): boolean {
	if (!browser) return false;
	if (!posthogKey()) return false;
	return readStoredConsent() === null;
}

export function acceptAnalyticsConsent(): void {
	if (!browser) return;
	initPosthogBrowser();
	if (!posthogKey()) return;
	posthog.opt_in_capturing();
	_identifyDistinctFromStorage();
	writeStoredConsent('accepted');
	posthog.capture('analytics_consent_accepted', { consent_version: CONSENT_VERSION });
}

export function declineAnalyticsConsent(): void {
	if (!browser) return;
	initPosthogBrowser();
	if (!posthogKey()) return;
	posthog.opt_out_capturing();
	writeStoredConsent('declined');
}

export function captureEvent(event: string, properties?: Record<string, unknown>): void {
	if (!browser) return;
	initPosthogBrowser();
	if (!posthogKey()) return;
	if (!posthog.has_opted_in_capturing()) return;
	posthog.capture(event, properties);
}

export function capturePageview(url: string): void {
	captureEvent('$pageview', { $current_url: url });
}
