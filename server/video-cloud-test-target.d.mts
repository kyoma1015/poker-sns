export const CLOUD_TEST_REF: string
export const CLOUD_TEST_URL: string
export function assertCloudTestTarget(env: Record<string, string | undefined>): Readonly<{projectRef: string; url: string}>
export function assertCloudTestRequestConfiguration(env: Record<string, string | undefined>): Readonly<{projectRef: string; url: string}> | null
