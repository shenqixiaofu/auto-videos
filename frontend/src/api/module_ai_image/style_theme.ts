import request from "@/utils/request";

const API_PATH = "/ai_image/style_theme";

const AiStyleThemeAPI = {
  // 列表查询
  listAiStyleTheme(query: AiStyleThemePageQuery) {
    return request<ApiResponse<PageResult<AiStyleThemeTable[]>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  // 详情查询
  detailAiStyleTheme(id: number) {
    return request<ApiResponse<AiStyleThemeTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  // 新增
  createAiStyleTheme(body: AiStyleThemeForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  // 修改（带主键）
  updateAiStyleTheme(id: number, body: AiStyleThemeForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  // 删除（支持批量）
  deleteAiStyleTheme(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: ids,
    });
  },

  // 批量启用/停用
  batchAiStyleTheme(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/available/setting`,
      method: "patch",
      data: body,
    });
  },

  // 导出
  exportAiStyleTheme(query: AiStyleThemePageQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: "post",
      data: query,
      responseType: "blob",
    });
  },

  // 下载导入模板
  downloadTemplateAiStyleTheme() {
    return request<Blob>({
      url: `${API_PATH}/download/template`,
      method: "post",
      responseType: "blob",
    });
  },

  // 导入
  importAiStyleTheme(body: FormData) {
    return request<ApiResponse>({
      url: `${API_PATH}/import`,
      method: "post",
      data: body,
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // 🌟 新增：调用大模型生成风格参数
  generateStyleParams(data: AiStyleThemeGenerateForm) {
    return request<ApiResponse<AiStyleThemeGenerateResult>>({
      url: `${API_PATH}/generate_params`, // 对应后端 controller 的路由
      timeout: 600000,
      method: "post",
      data: data, // POST 请求使用 data 传递 body
    });
  },
};

export default AiStyleThemeAPI;

// ------------------------------
// TS 类型声明
// ------------------------------

export interface AiStyleThemeGenerateForm {
  gender: string; // 性别 (如: male/female/any)
  theme_name: string; // 主题名称 (如: 井冈山小红军)
  remark?: string; // 补充说明 (可选)
}

// 2. 定义大模型返回的结果类型
export interface AiStyleThemeGenerateResult {
  material: string; // 材质描述
  clothing_style: string; // 穿着风格描述
  colors: string; // 配色方案
  vibe: string; // 氛围感关键词
  remark: string; // AI给出的建议/备注
}

// 列表查询参数
export interface AiStyleThemePageQuery extends PageQuery {
  theme_name?: string;
  material?: string;
  clothing_style?: string;
  colors?: string;
  gender: string;
  vibe?: string;
  status?: string;
  remark?: string;
  created_id?: number;
  updated_id?: number;
  created_time?: string[];
  updated_time?: string[];
}

// 列表展示项
export interface AiStyleThemeTable extends BaseType {
  theme_name?: string;
  material?: string;
  clothing_style?: string;
  gender?: string;
  colors?: string;
  vibe?: string;
  remark?: string;
  created_id?: string;
  updated_id?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
}

// 新增/修改/详情表单参数
export interface AiStyleThemeForm extends BaseFormType {
  theme_name?: string;
  material?: string;
  gender?: string;
  clothing_style?: string;
  colors?: string;
  vibe?: string;
  remark?: string;
}
