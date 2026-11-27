import type { SupabaseClient } from '@supabase/supabase-js'

export function videoBudgetRequired(): boolean
export function videoBudgetCredential(
  viewer: SupabaseClient,
  url: string,
  anon: string,
  viewerAuthorization: string,
  operation: 'media' | 'finalize' | 'inspect',
): Promise<string>
