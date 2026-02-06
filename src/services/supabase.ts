import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

// Debug logs to verify env loading (values are masked)
console.log("Supabase URL loaded:", !!supabaseUrl);
console.log("Supabase Anon Key loaded:", !!supabaseAnonKey);

if (!supabaseUrl || !supabaseAnonKey) {
	console.error(
		"CRITICAL: Supabase credentials missing! Check .env.local and vite.config.ts prefixes.",
	);
}

export const supabase = createClient(
	supabaseUrl || "https://placeholder-url-missing.supabase.co",
	supabaseAnonKey || "placeholder-key-missing",
);
