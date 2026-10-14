import request from "@/utils/request";

const API_PATH = "/ai_image/auto_strategy";

const AiImageAutoStrategyAPI = {
  // 列表查询
  listAiImageAutoStrategy(query: AiImageAutoStrategyPageQuery) {
    return request<ApiResponse<PageResult<AiImageAutoStrategyTable[]>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  // 详情查询
  detailAiImageAutoStrategy(id: number) {
    return request<ApiResponse<AiImageAutoStrategyTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  // 新增
  createAiImageAutoStrategy(body: AiImageAutoStrategyForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  // 修改（带主键）
  updateAiImageAutoStrategy(id: number, body: AiImageAutoStrategyForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  // 删除（支持批量）
  deleteAiImageAutoStrategy(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: ids,
    });
  },

  // 批量启用/停用
  batchAiImageAutoStrategy(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/available/setting`,
      method: "patch",
      data: body,
    });
  },

  // 导出
  exportAiImageAutoStrategy(query: AiImageAutoStrategyPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: "post",
      data: query,
      responseType: "blob",
    });
  },

  // 下载导入模板
  downloadTemplateAiImageAutoStrategy() {
    return request<Blob>({
      url: `${API_PATH}/download/template`,
      method: "post",
      responseType: "blob",
    });
  },

  // 导入
  importAiImageAutoStrategy(body: FormData) {
    return request<ApiResponse>({
      url: `${API_PATH}/import`,
      method: "post",
      data: body,
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

export default AiImageAutoStrategyAPI;

// ------------------------------
// TS 类型声明
// ------------------------------

// 列表查询参数
export interface AiImageAutoStrategyPageQuery extends PageQuery {
  strategy_name?: string;
  location?: string;
  gender?: string;
  age_min?: string;
  age_max?: string;
  daily_batch_limit?: string;
  priority?: string;
  status?: string;
  created_id?: number;
  updated_id?: number;
  created_time?: string[];
  updated_time?: string[];
}

// 列表展示项
export interface AiImageAutoStrategyTable extends BaseType {
  strategy_name?: string;
  location?: string;
  gender?: string;
  age_min?: string;
  age_max?: string;
  daily_batch_limit?: string;
  priority?: string;
  created_id?: string;
  updated_id?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
}

// 新增/修改/详情表单参数
export interface AiImageAutoStrategyForm extends BaseFormType {
  strategy_name?: string;
  location?: string;
  gender?: string;
  theme_ids: number[];
  background_strategy?: string;
  age_min?: number;
  age_max?: number;
  daily_batch_limit?: string;
  priority?: string;
}
