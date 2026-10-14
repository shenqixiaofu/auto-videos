import request from "@/utils/request";

const API_PATH = "/ai_image/fission";

// 视觉反推请求参数
export interface InferBackgroundParams {
  image_url?: string; // 参考图 URL（可选）
  location?: string; // 目标地点（可选）
}

export const FissionTaskAPI = {
  /**
   * 🔍 获取单张图片的详细信息 (用于编辑页数据回显)
   */
  getTaskDetail(taskId: number | string) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/task/${taskId}`,
      method: "get",
    });
  },
  // 👇 把这个贴到 FissionTaskAPI 对象里面
  /**
   * 👁️‍🗨️ 调用多模态大模型，反推背景并生成光影重配参数
   */
  inferBackground(data: InferBackgroundParams) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/task/infer-background`, // 对应你后端的实际路由
      method: "post",
      data: data,
      // 🚀 60000ms = 60秒。因为大模型“看图写小作文”通常需要 5~20 秒，给足宽裕度
      timeout: 60000,
    });
  },
  /**
   * 🧠 专家创作台：调用大模型脑暴 15 组生图底层指令
   */
  brainstormExpertPrompts(data: {
    location: string;
    gender: string;
    age: number;
    theme?: any;
    extra_command?: string;
  }) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/expert/brainstorm`, // 确保这里和你的 Router 路径一致
      method: "post",
      data: data,
      timeout: 300000, // 🚀 强烈建议加 300s 超时！一次性生成 15 组复杂的 JSON 数据耗时较长
    });
  },

  /**
   * 🚀 专家创作台：提交已确认的 15 组底层指令入库，进入 ComfyUI 队列
   */
  submitExpertTask(data: {
    location: string;
    gender: string;
    age: number;
    theme?: string;
    selected_scene: string;
    selected_style: string;
    tasks: Array<{
      view_type: string;
      action_desc: string;
      positive_prompt: string;
    }>;
  }) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/expert/submit`, // 对应你后端的 /expert/submit 路由
      method: "post",
      data: data,
      // 纯数据库操作，无需超长 timeout，走系统默认即可
    });
  },

  /**
   * 🚀 一键高清 (图像超分)
   * ⚠️ 涉及火山引擎调用和 MinIO 图片拉取，适当放宽超时时间
   */
  upscaleTask(data: {
    task_id: number | string;
    model_quality?: string;
    result_format?: number;
    jpg_quality?: number;
  }) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/task/upscale`,
      method: "post",
      data: data,
      timeout: 30000, // 火山引擎超分可能需要几秒到十几秒
    });
  },

  /**
   * ✨ 图生图精修重绘 (预留给你接下来的编辑页提交按钮)
   */
  // 👇 优化这里的入参类型声明
  regenerateTask(data: {
    task_id: number | string;
    params: Record<string, any>; // 🚀 接收包含各种微调参数的对象
    is_new_version: boolean; // 🚀 标记是否生成 v2/v3
  }) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/task/regenerate`,
      method: "post",
      data: data,
      timeout: 60000, // 生成图片时间长，保持 60s 超时是对的
    });
  },
  /**
   * 🎭 极速换脸：调用火山引擎 API 直接融合面部并转存
   */
  faceSwapTask(data: {
    task_id: number | string;
    target_face_url: string; // 🚀 用户上传的真人面部图 URL
    target_url: string;
  }) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/task/face-swap`,
      method: "post",
      data: data,
      // 火山 API 处理通常只要 2-5 秒，但咱们后端还要把它下载并转存到自家 MinIO，
      // 所以给个 30 秒超时比较稳妥，防止网络波动导致前端转圈圈报错断开。
      timeout: 30000,
    });
  },
  /**
   * 💾 更新任务数据 (回填 URL 或保存 Prompt)
   */
  updateTask(taskId: number | string, data: any) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/task/${taskId}`,
      method: "put",
      data: data,
    });
  },

  /**
   * 🖼️ 背景瞬移 (图像融合)
   * 将当前任务的人物图与新上传的背景图进行 AI 融合，支持自定义提示词
   */
  backgroundFusionTask(data: {
    task_id: number | string;
    bg_image_url: string;
    custom_prompt: string;
    model: string;
  }) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/task/background-fusion`,
      method: "post",
      data: data, // 🚀 直接把整个对象丢给后端
      timeout: 3000000, // 融合慢，保留你的超长超时设置
    });
  },
  /**
   * 🎨 专家重绘：针对单张图片修改提示词后重新生成
   */
  regenerateExpertTask(data: { task_id: number; positive_prompt: string; params?: any }) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/task/regenerate-expert`,
      method: "post",
      data,
    });
  },
};

export default FissionTaskAPI;
