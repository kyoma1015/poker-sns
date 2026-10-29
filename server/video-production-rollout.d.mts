export function assertProductionVideoPublisher(viewer: { rpc(name: string): PromiseLike<{data: unknown; error: unknown}> }, userId: string): Promise<void>;
export function assertProductionVideoConfiguration(): void;
