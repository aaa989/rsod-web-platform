import request from "../utils/request";

// 单图检测接口
export const detectSingleImage = (data) => {
  return request({
    url: "/detection/single",
    method: "post",
    data,
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

// 获取检测历史
export const getDetectionHistory = (params) => {
  return request({
    url: "/detection/history",
    method: "get",
    params,
  });
};

// 获取检测详情
export const getDetectionDetail = (id) => {
  return request({
    url: `/detection/detail/${id}`,
    method: "get",
  });
};

// 获取目标库列表
export const getTargetList = () => {
  return request({
    url: "/targets/list",
    method: "get",
  });
};

// 新增：摄像头帧检测接口（核心）
export const detectCameraFrame = (data) => {
  return request({
    url: "/detection/camera/detect",
    method: "post",
    data, // 这里不需要特殊headers，因为传的是base64字符串（JSON格式）
  });
};
