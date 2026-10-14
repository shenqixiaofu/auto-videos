import request from "@/utils/request";

const API_PATH = "/common/file";

export const FileAPI = {
  /**
   * 上传文件
   * @param formData 文件数据
   */
  uploadFile(formData: FormData) {
    return request<ApiResponse<FileUploadSchema>>({
      url: `${API_PATH}/upload`,
      method: "post",
      data: formData,
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

/**
 * 资源上传响应模型
 */
export interface FileUploadSchema {
  /** 文件名 */
  filename: string;
  /** 访问URL */
  file_url: string;
  /** 文件大小 */
  file_size: number;
  /** 上传时间 */
  upload_time: string;
}
