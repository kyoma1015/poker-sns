import { assertCurrentVideoCloudTestClient } from './videoCloudTestGuard'
import { videoStorageFetch } from './videoUploadTransport'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// Fence before createClient can restore or refresh any persisted session.
assertCurrentVideoCloudTestClient()

export const supabase = createClient(supabaseUrl, supabaseKey, {
  global: { fetch: videoStorageFetch },
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})
