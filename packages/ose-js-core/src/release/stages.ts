import type { BuildStep, Release } from "../model";

/** The stages of the build configuration the release runs */
export function releaseStages(release: Release<any> | null | undefined): BuildStep[] {
    return release?.context?.build_configuration.stages ?? [];
}

/**
 * Index of the stage that runs or ran last. The stored context is only updated after each stage, so the progress
 * reveals which stage runs.
 */
export function currentStage(release: Release<any> | null | undefined): number {
    const stage = release?.context?.current_stage ?? 0;
    return release?.state === "running" ? Math.max(stage, release.progress?.stage ?? 0) : stage;
}

export interface StageDetails {
    [K: string]: any
    errors?: any[]
    warnings?: any[]
    infos?: any[]
    __progress?: {
        position?: [number, number]
        progress: number
        current_item?: string
        message?: string
    }
}

/**
 * The data, diagnostics, and progress of a stage of the release, or null if the stage did not start yet
 */
export function stageDetails(release: Release<any> | null | undefined, stage: number): StageDetails | null {
    const result = release?.context?.stage_results[stage];
    const details: StageDetails = result ? {
        ...result.data,
        errors: result.log.errors,
        warnings: result.log.warnings,
        infos: result.log.infos,
    } : {};

    const progress = release?.progress;
    if (release?.state === "running" && progress?.stage === stage && progress.current_item !== null) {
        // A negative item means the stage did not start on its first item yet
        const position = progress.current_item + 1;
        const known = progress.current_item >= 0 && progress.total_items !== null;
        details.__progress = {
            position: known ? [position, progress.total_items!] : undefined,
            progress: known && progress.total_items ? position / progress.total_items : 0,
            current_item: progress.item ?? undefined,
            message: progress.message ?? undefined,
        };
    }

    return Object.keys(details).length > 0 ? details : null;
}
