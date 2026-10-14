import request from "@/utils/request";

// ⚠️ 这里的路径请根据你在后端 controller 里的实际映射前缀调整
// 框架默认可能会把 module_ai_image 映射为 /ai_image
const API_PATH = "/ai_image/fission";

// ==========================================
// 1. 类型定义 (Type Definitions) - 对齐后端 Schema
// ==========================================

// 提交生成的表单参数
export interface FissionCreateForm {
  location: string;
  gender: string;
  age: number;
}

// 列表查询参数
export interface FissionPageQuery {
  page?: number; // 或 pageNum，看你们框架底层封装
  page_size?: number; // 或 pageSize
  input_location?: string;
  batch_sn?: string;
}

// 批次列表的数据结构
export interface BatchTable {
  id: number;
  uuid: string;
  batch_sn: string;
  input_location: string;
  gender: string;
  age: number;
  selected_scene?: string;
  selected_style?: string;
  task_count: number;
  created_time: string;
}

// 任务明细的数据结构
export interface TaskTable {
  id: number;
  uuid: string;
  task_sn: string;
  view_type?: string;
  action_desc?: string;
  positive_prompt: string;
  process_status: number; // 0待抢单 1生成中 2成功 3失败
  image_url?: string;
  agent_id?: string;
  created_time: string;
  completed_at?: string;
}

// ==========================================
// 2. API 接口封装 (API Object)
// ==========================================

export const FissionBatchAPI = {
  /**
   * 触发黄金模板裂变 (生成一个新批次)
   * ⚠️ 注意：涉及 LLM 思考，超时 60s
   */
  generateFissionTask(data: FissionCreateForm) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/generate`,
      method: "post",
      data: data,
      timeout: 60000,
    });
  },

  /**
   * 获取历史策划底片台的批次列表
   */
  getBatchList(query: FissionPageQuery) {
    return request<any, ApiResponse<PageResult<BatchTable[]>>>({
      url: `${API_PATH}/batch/list`,
      method: "get",
      params: query,
    });
  },

  /**
   * 获取某个批次下的 10 个生图任务详情
   * (虽然返回的是 Task，但入口是 Batch ID，所以放在这里很合适)
   */
  getBatchTasks(batchId: number) {
    return request<ApiResponse<TaskTable[]>>({
      url: `${API_PATH}/batch/${batchId}/tasks`,
      method: "get",
    });
  },

  /**
   * 🚀 一次性获取所有检索下拉选项 (聚合接口)
   */
  /**
   * 获取所有筛选项（支持基于性别等条件的联动查询）
   * @param params 包含 gender 等可选过滤参数
   */
  getAllFilterOptions(params?: { gender?: string; [key: string]: any }) {
    return request<
      ApiResponse<{
        locations: string[];
        scenes: string[];
        styles: string[];
        themes: string[];
      }>
    >({
      url: `${API_PATH}/batch/filter-options`,
      method: "get",
      params, // 将参数透传，Axios 会自动处理成 Query String
    });
  },

  /**
   * 销毁指定的生图批次及其所有关联任务
   * @param id 批次ID
   */
  deleteBatch(id: number | string) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/batch/${id}`,
      method: "delete",
    });
  },

  /**
   * 手动补录裂变批次
   * @param data 包含地点、人群信息及 MinIO URL 数组
   */
  manualBatchCreate(data: {
    input_location: string;
    gender: string;
    age: number;
    theme: string;
    selected_scene: string;
    selected_style: string;
    image_urls: string[];
  }) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/batch/manual`,
      method: "post",
      data, // JSON 格式提交
    });
  },

  /**
   * 🔍 获取生图批次详情及任务列表 (专用于工作台 URL 状态回显)
   * @param batchId 批次自增 ID
   */
  getBatchDetail(batchId: number) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/batch/${batchId}`,
      method: "get",
    });
  },
};

export default FissionBatchAPI;
