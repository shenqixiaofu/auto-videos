import axios from "axios";
import request from "@/utils/request";

const API_PATH = "/video/processing/tasks";

/** 视频素材用途 */
export type VideoAssetRole =
  | "source"
  | "cover"
  | "ending"
  | "music"
  | "review"
  | "output"
  | "subtitle";

/** 输出画面比例 */
export type VideoAspectRatio = "9:16";

/** 自动剪辑风格预设 */
export type VideoStylePreset = "vlog" | "travel" | "food" | "clean";

/** 风格预设展示名，新建表单与任务详情共用一份，避免两处各写一套标签。 */
export const VIDEO_STYLE_PRESET_OPTIONS: Array<{ label: string; value: VideoStylePreset }> = [
  { label: "日常 Vlog", value: "vlog" },
  { label: "旅行记录", value: "travel" },
  { label: "美食探店", value: "food" },
  { label: "清爽简约", value: "clean" },
];

/** 自动剪辑任务状态 */
export type VideoTaskStatus =
  | "draft"
  | "uploading"
  | "queued"
  | "processing"
  | "reviewing"
  | "succeeded"
  | "failed"
  | "cancelled";

/** 自动剪辑处理阶段 */
export type VideoTaskStage =
  | "draft"
  | "uploading"
  | "queued"
  | "media_analysis"
  | "transcription"
  | "editing"
  | "rendering"
  | "quality_check"
  | "reviewing"
  | "completed";

/** 封面生图通道：relay=OpenAI 协议中转站，seedream=火山方舟 */
export type VideoCoverImageProvider = "relay" | "seedream";

/** 创建任务参数 */
export interface VideoTaskCreateParams {
  title: string;
  aspect_ratio: VideoAspectRatio;
  style_preset: VideoStylePreset;
  batch_id?: number;
  batch_index?: number;
}

/** 素材分片上传初始化参数 */
export interface VideoAssetInitiateParams {
  asset_role: "source" | "ending";
  file_name: string;
  content_type: string;
  file_size: number;
}

/** 单个预签名分片 */
export interface VideoUploadPart {
  part_number: number;
  upload_url: string;
}

/** 素材分片上传会话 */
export interface VideoMultipartSession {
  asset_id: number;
  upload_id: string;
  bucket: string;
  object_key: string;
  part_size: number;
  parts: VideoUploadPart[];
}

/** 已上传分片 */
export interface VideoCompletedPart {
  part_number: number;
  etag: string;
}

/** 完成素材上传参数 */
export interface VideoAssetCompleteParams {
  upload_id: string;
  parts: VideoCompletedPart[];
}

/** 待审核成片操作 */
export interface VideoTaskReviewParams {
  action: "approve" | "regenerate";
  adjustment_prompt?: string;
}

/** 刷新指定分片上传签名参数 */
export interface VideoAssetPartsSignParams {
  upload_id: string;
  part_numbers: number[];
}

/** 任务素材 */
export interface VideoTaskAsset {
  id: number;
  task_id: number;
  asset_role: VideoAssetRole;
  file_name: string;
  file_size: number;
  content_type: string;
  file_metadata: Record<string, unknown>;
  bucket: string;
  object_key: string;
  upload_id: string | null;
  upload_status: "pending" | "uploading" | "completed" | "failed";
  etag: string | null;
  created_time: string;
  updated_time: string;
}

/** 单次渲染实际用到的变量摘要 */
export interface VideoTaskDebugSummary {
  style_preset?: VideoStylePreset;
  sticker_theme_id?: string | null;
  sticker_templates?: string[];
  sticker_count?: number;
  animation_count?: number;
  graphic_sticker_count?: number;
  graphic_sticker_tones?: string[];
  transitions?: string[];
  subtitle_count?: number;
  highlight_keyword_count?: number;
  bgm_title?: string | null;
  bgm_tag?: string | null;
  audio_mix?: {
    voice_loudness_target?: number;
    bgm_loudness_target?: number;
    true_peak?: number;
  } | null;
  render_provider?: string | null;
  render_id?: string | null;
  models?: Record<string, string>;
}

/** 单个处理阶段的耗时 */
export interface VideoTaskStageTiming {
  stage: string;
  label?: string;
  elapsed_seconds?: number;
  /** 与主链并行的阶段，不计入合计耗时 */
  parallel?: boolean;
}

/** 当前正在处理的阶段。elapsed_seconds 是响应生成那一刻的已耗时，
 *  前端拿到后本地继续累加，用户不刷新也能看到数字在涨。 */
export interface VideoTaskStageProgress {
  stage: string;
  label?: string;
  started_at?: string;
  elapsed_seconds?: number;
}

/** 任务处理参数 */
export interface VideoTaskConfig {
  aspect_ratio: VideoAspectRatio;
  style_preset: VideoStylePreset;
  cover_image_provider?: VideoCoverImageProvider | null;
  attempt_started_time?: string | null;
  debug_summary?: VideoTaskDebugSummary | null;
  stage_timings?: VideoTaskStageTiming[] | null;
  stage_progress?: VideoTaskStageProgress | null;
}

/** 自动剪辑任务 */
export interface VideoProcessingTask {
  id: number;
  task_no: string;
  title: string;
  batch_id: number;
  batch_index: number;
  status: VideoTaskStatus;
  current_stage: VideoTaskStage;
  progress: number;
  config: VideoTaskConfig;
  error_message: string | null;
  cover_preview_url: string | null;
  created_time: string;
  updated_time: string;
  finished_time: string | null;
}

/** 自动剪辑任务详情 */
export interface VideoProcessingTaskDetail extends VideoProcessingTask {
  assets: VideoTaskAsset[];
}

/** 自动剪辑批次创建参数 */
export interface VideoProcessingBatchCreateParams {
  batch_name: string;
  batch_type: "single" | "folder";
  expected_count: number;
}

/** 自动剪辑批次 */
export interface VideoProcessingBatch {
  id: number;
  batch_no: string;
  batch_name: string;
  batch_type: "single" | "folder";
  expected_count: number;
  task_count: number;
  completed_count: number;
  status: VideoTaskStatus;
  current_stage: VideoTaskStage;
  progress: number;
  error_message: string | null;
  cover_preview_url: string | null;
  created_time: string;
  updated_time: string;
  finished_time: string | null;
  // 列表只返回任务摘要，素材与完整渲染元数据需要另拉任务详情。
  tasks: VideoProcessingTask[];
}

/** 自动剪辑全局配置（管理员高级设置）。提示词模板为空表示用代码内置默认。 */
export interface VideoProcessingConfig {
  cover_image_provider: VideoCoverImageProvider;
  relay_image_model: string;
  relay_image_size: string;
  cover_summary_model: string;
  creative_planner_model: string;
  cover_prompt_template: string | null;
  planner_prompt_template: string | null;
  /** 封面策划拆两段：system 管角色与调性，user 管输入与 JSON 契约 */
  cover_plan_prompt_template: string | null;
  cover_plan_user_prompt_template: string | null;
  /** 标题风格样本，一行一条 */
  cover_style_samples: string | null;
  cover_title_max_chars: number;
  cover_subtitle_max_chars: number;
  cover_badge_max_chars: number;
  cover_highlight_count: number;
  /** 底部字幕样式。字号上限受贴纸装饰带几何约束，后端也会夹取。 */
  subtitle_font: string;
  subtitle_font_size: number;
  subtitle_outline_width: number;
  subtitle_bold: boolean;
  /** 内置默认原文，只读。留空=跟随默认，所以要靠它把编辑框铺满。 */
  cover_prompt_template_default: string;
  planner_prompt_template_default: string;
  cover_plan_prompt_template_default: string;
  cover_plan_user_prompt_template_default: string;
  cover_style_samples_default: string;
  cover_title_max_chars_default: number;
  cover_subtitle_max_chars_default: number;
  cover_badge_max_chars_default: number;
  cover_highlight_count_default: number;
  subtitle_font_default: string;
  subtitle_font_size_default: number;
  subtitle_outline_width_default: number;
  subtitle_bold_default: boolean;
  /** 字体下拉候选由后端下发：阿里对写错的字体名是静默回落，前端不自己维护一份。 */
  subtitle_font_options: string[];
  version: number;
  updated_time: string | null;
  updated_by: string | null;
}

/** 更新全局配置。只提交要改的字段，传 null 表示恢复默认。 */
export type VideoProcessingConfigUpdateParams = Partial<
  Omit<
    VideoProcessingConfig,
    | "version"
    | "updated_time"
    | "updated_by"
    | "cover_prompt_template_default"
    | "planner_prompt_template_default"
    | "cover_plan_prompt_template_default"
    | "cover_plan_user_prompt_template_default"
    | "cover_style_samples_default"
    | "cover_title_max_chars_default"
    | "cover_subtitle_max_chars_default"
    | "cover_badge_max_chars_default"
    | "cover_highlight_count_default"
    | "subtitle_font_default"
    | "subtitle_font_size_default"
    | "subtitle_outline_width_default"
    | "subtitle_bold_default"
    | "subtitle_font_options"
  >
>;

/** 中转站支持生图的模型清单，用于高级设置里的模型下拉 */
export interface VideoCoverImageModel {
  name: string;
  endpoint_types: string[];
}

/** 任务调试信息：本次实际用到的提示词与生图参考帧。老任务字段为 null。 */
export interface VideoTaskDebugInfo {
  planner_model: string | null;
  planner_system_prompt: string | null;
  planner_user_prompt: string | null;
  cover_image_provider: string | null;
  cover_image_model: string | null;
  cover_image_size: string | null;
  cover_summary_model: string | null;
  cover_image_prompt: string | null;
  cover_prompt: string | null;
  cover_reference_url: string | null;
  cover_reference_name: string | null;
}

/** 批次列表查询参数 */
export interface VideoBatchListParams extends PageQuery {
  status?: VideoTaskStatus;
  keyword?: string;
  batch_type?: "single" | "folder";
}

/** 分片上传进度 */
export interface VideoMultipartProgress {
  uploaded_bytes: number;
  total_bytes: number;
  percent: number;
}

/** 短期产物访问地址 */
export interface VideoAssetDownloadUrl {
  url: string;
  expires_in: number;
}

/** 单个素材的完整媒体元数据。详情接口不下发 file_metadata（完整时间线 JSON 太大），
 *  前端展开折叠区时走 assets/{id}/metadata 单独取。 */
export interface VideoAssetMetadata {
  asset_id: number;
  asset_role: VideoAssetRole;
  file_metadata: Record<string, unknown>;
}

export const VideoProcessingAPI = {
  /** 创建自动剪辑任务 */
  createTask(data: VideoTaskCreateParams) {
    return request<ApiResponse<VideoProcessingTaskDetail>>({
      url: API_PATH,
      method: "post",
      data,
    });
  },

  /** 创建自动剪辑批次 */
  createBatch(data: VideoProcessingBatchCreateParams) {
    return request<ApiResponse<VideoProcessingBatch>>({
      url: `${API_PATH.replace("/tasks", "")}/batches`,
      method: "post",
      data,
    });
  },

  /** 初始化指定素材的 Multipart 上传 */
  initiateAsset(taskId: number, data: VideoAssetInitiateParams) {
    return request<ApiResponse<VideoMultipartSession>>({
      url: `${API_PATH}/${taskId}/assets/initiate`,
      method: "post",
      data,
    });
  },

  /** 通知服务端合并已上传的素材分片 */
  completeAsset(taskId: number, assetId: number, data: VideoAssetCompleteParams) {
    return request<ApiResponse<VideoTaskAsset>>({
      url: `${API_PATH}/${taskId}/assets/${assetId}/complete`,
      method: "post",
      data,
    });
  },

  /** 刷新长时间上传任务中尚未开始的分片签名 */
  refreshAssetParts(taskId: number, assetId: number, data: VideoAssetPartsSignParams) {
    return request<ApiResponse<VideoUploadPart[]>>({
      url: `${API_PATH}/${taskId}/assets/${assetId}/parts/sign`,
      method: "post",
      data,
    });
  },

  /** 中止失败素材的 Multipart 上传 */
  abortAsset(taskId: number, assetId: number) {
    return request<ApiResponse<VideoTaskAsset>>({
      url: `${API_PATH}/${taskId}/assets/${assetId}/abort`,
      method: "post",
    });
  },

  /** 提交素材完整的任务进入处理队列 */
  submitTask(taskId: number) {
    return request<ApiResponse<VideoProcessingTaskDetail>>({
      url: `${API_PATH}/${taskId}/submit`,
      method: "post",
    });
  },

  /** 分页查询自动剪辑批次 */
  getBatches(params: VideoBatchListParams) {
    return request<ApiResponse<PageResult<VideoProcessingBatch[]>>>({
      url: `${API_PATH.replace("/tasks", "")}/batches`,
      method: "get",
      params,
    });
  },

  /** 查询自动剪辑任务详情 */
  getTask(taskId: number) {
    return request<ApiResponse<VideoProcessingTaskDetail>>({
      url: `${API_PATH}/${taskId}`,
      method: "get",
    });
  },

  /** 取消自动剪辑任务 */
  cancelTask(taskId: number) {
    return request<ApiResponse<VideoProcessingTaskDetail>>({
      url: `${API_PATH}/${taskId}/cancel`,
      method: "post",
    });
  },

  /** 重试失败或已取消的任务 */
  retryTask(taskId: number) {
    return request<ApiResponse<VideoProcessingTaskDetail>>({
      url: `${API_PATH}/${taskId}/retry`,
      method: "post",
    });
  },

  /** 审核通过或重新生成待确认成片 */
  reviewTask(taskId: number, data: VideoTaskReviewParams) {
    return request<ApiResponse<VideoProcessingTaskDetail>>({
      url: `${API_PATH}/${taskId}/review`,
      method: "post",
      data,
    });
  },

  /** 获取输出视频或字幕的短期访问地址 */
  getAssetDownloadUrl(taskId: number, assetId: number, download = false) {
    return request<ApiResponse<VideoAssetDownloadUrl>>({
      url: `${API_PATH}/${taskId}/assets/${assetId}/download`,
      method: "get",
      params: { download },
    });
  },

  /** 按需获取单个素材的完整媒体元数据（含完整时间线 JSON） */
  getAssetMetadata(taskId: number, assetId: number) {
    return request<ApiResponse<VideoAssetMetadata>>({
      url: `${API_PATH}/${taskId}/assets/${assetId}/metadata`,
      method: "get",
    });
  },

  /** 获取任务调试信息（本次实际使用的提示词与生图参考帧） */
  getTaskDebug(taskId: number) {
    return request<ApiResponse<VideoTaskDebugInfo>>({
      url: `${API_PATH}/${taskId}/debug`,
      method: "get",
    });
  },

  /** 查询自动剪辑全局配置（管理员） */
  getProcessingConfig() {
    return request<ApiResponse<VideoProcessingConfig>>({
      url: `${API_PATH.replace("/tasks", "")}/config`,
      method: "get",
    });
  },

  /** 保存自动剪辑全局配置，字段传 null 表示恢复默认 */
  updateProcessingConfig(data: VideoProcessingConfigUpdateParams) {
    return request<ApiResponse<VideoProcessingConfig>>({
      url: `${API_PATH.replace("/tasks", "")}/config`,
      method: "put",
      data,
    });
  },

  /** 查询中转站当前支持生图的模型清单，拉不到时返回空数组 */
  getCoverImageModels() {
    return request<ApiResponse<VideoCoverImageModel[]>>({
      url: `${API_PATH.replace("/tasks", "")}/config/image-models`,
      method: "get",
    });
  },
};

/**
 * 将文件直接上传到服务端返回的 MinIO 预签名地址。
 * 固定使用三个并发上传器，避免大文件分片一次性占满浏览器连接。
 */
export async function uploadVideoMultipart(
  file: File,
  session: VideoMultipartSession,
  onProgress?: (progress: VideoMultipartProgress) => void,
  refreshParts?: (partNumbers: number[]) => Promise<VideoUploadPart[]>
): Promise<VideoCompletedPart[]> {
  const sortedParts = [...session.parts].sort(
    (left, right) => left.part_number - right.part_number
  );
  const partProgress = new Map<number, number>();
  const completedParts: VideoCompletedPart[] = [];
  let nextPartIndex = 0;

  const emitProgress = () => {
    const uploadedBytes = Array.from(partProgress.values()).reduce(
      (total, size) => total + size,
      0
    );
    onProgress?.({
      uploaded_bytes: uploadedBytes,
      total_bytes: file.size,
      percent: Math.min(100, Math.round((uploadedBytes / file.size) * 100)),
    });
  };

  const uploadNextPart = async (): Promise<void> => {
    const currentIndex = nextPartIndex;
    nextPartIndex += 1;

    if (currentIndex >= sortedParts.length) {
      return;
    }

    const part = sortedParts[currentIndex];
    const start = (part.part_number - 1) * session.part_size;
    const blob = file.slice(start, Math.min(start + session.part_size, file.size));
    partProgress.set(part.part_number, 0);

    const uploadPart = (uploadUrl: string) =>
      axios.put(uploadUrl, blob, {
        headers: { "Content-Type": file.type },
        onUploadProgress: (event) => {
          partProgress.set(part.part_number, Math.min(event.loaded, blob.size));
          emitProgress();
        },
      });

    let uploadUrl = part.upload_url;
    if (currentIndex >= 3 && refreshParts) {
      const [refreshedPart] = await refreshParts([part.part_number]);
      uploadUrl = refreshedPart.upload_url;
    }

    let response;
    try {
      response = await uploadPart(uploadUrl);
    } catch (error) {
      const status = axios.isAxiosError(error) ? error.response?.status : undefined;
      if (!refreshParts || !status || ![400, 403].includes(status)) throw error;
      const [refreshedPart] = await refreshParts([part.part_number]);
      response = await uploadPart(refreshedPart.upload_url);
    }
    const etag = response.headers.etag;

    if (!etag) {
      throw new Error(`分片 ${part.part_number} 未返回 ETag，请检查 MinIO CORS 配置`);
    }

    partProgress.set(part.part_number, blob.size);
    completedParts.push({ part_number: part.part_number, etag });
    emitProgress();
    await uploadNextPart();
  };

  const workerCount = Math.min(3, sortedParts.length);
  await Promise.all(Array.from({ length: workerCount }, () => uploadNextPart()));
  return completedParts.sort((left, right) => left.part_number - right.part_number);
}

export default VideoProcessingAPI;
