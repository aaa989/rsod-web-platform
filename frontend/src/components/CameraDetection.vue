<template>
  <div class="camera-detection-container">
    <div class="camera-controls mb-4">
      <el-button
        type="primary"
        @click="startOrStopCamera"
        :disabled="isLoading"
      >
        {{ isRunning ? "停止摄像头" : "启动摄像头" }}
      </el-button>
      <el-button
        type="warning"
        @click="togglePause"
        :disabled="!isRunning || isLoading"
        class="ml-2"
      >
        {{ isPaused ? "恢复检测" : "暂停检测" }}
      </el-button>

      <!-- 配置项 -->
      <el-select
        v-model="inferenceInterval"
        placeholder="推理间隔（帧）"
        class="ml-2 w-32"
        :disabled="isRunning"
      >
        <el-option label="每1帧" value="1"></el-option>
        <el-option label="每2帧" value="2"></el-option>
        <el-option label="每3帧" value="3"></el-option>
      </el-select>

      <el-select
        v-model="cameraId"
        placeholder="选择摄像头"
        class="ml-2 w-40"
        :disabled="isRunning"
      >
        <el-option label="默认摄像头" value="0"></el-option>
      </el-select>
    </div>

    <!-- 摄像头视频容器（视频+Canvas叠加） -->
    <div class="camera-view-container relative">
      <video
        ref="videoRef"
        class="camera-video"
        autoplay
        playsinline
        muted
      ></video>
      <canvas
        ref="canvasRef"
        class="camera-canvas absolute top-0 left-0"
      ></canvas>
      <!-- 捕获用的隐藏Canvas -->
      <canvas ref="captureCanvasRef" class="hidden"></canvas>
    </div>

    <!-- 统计信息 -->
    <div class="detection-stats mt-4">
      <el-descriptions :column="4" border>
        <el-descriptions-item label="当前帧率">
          {{ fps.toFixed(1) }} FPS
        </el-descriptions-item>
        <el-descriptions-item label="检测耗时">
          {{ (detectionTime * 1000).toFixed(0) }} ms
        </el-descriptions-item>
        <el-descriptions-item label="总帧数">
          {{ frameIndex }}
        </el-descriptions-item>
        <el-descriptions-item label="检测目标数">
          {{ totalObjects }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { detectCameraFrame } from "../api/detection";

// 核心状态
const videoRef = ref(null);
const canvasRef = ref(null);
const captureCanvasRef = ref(null);
const isRunning = ref(false);
const isPaused = ref(false);
const isLoading = ref(false);
const videoStream = ref(null);
const detectionFrameId = ref(null);
const currentBoxes = ref([]);
const lastDetectionTime = ref(0);
const consecutiveErrorCount = ref(0);

// 配置项
const cameraId = ref("0");
const inferenceInterval = ref("2"); // 每2帧检测一次
const frameIndex = ref(0);
const fps = ref(0);
const detectionTime = ref(0);
const totalObjects = ref(0);

// 启动/停止摄像头
const startOrStopCamera = async () => {
  if (isRunning.value) {
    // 停止摄像头
    await stopLocalCamera();
  } else {
    // 启动摄像头
    await startLocalCamera();
  }
};

// 启动本地摄像头
const startLocalCamera = async () => {
  try {
    isLoading.value = true;
    // 请求摄像头权限
    const constraints = {
      video: {
        deviceId: cameraId.value !== "0" ? cameraId.value : undefined,
        width: { ideal: 640 },
        height: { ideal: 480 },
        frameRate: { ideal: 30 },
      },
      audio: false,
    };

    // 获取视频流
    videoStream.value = await navigator.mediaDevices.getUserMedia(constraints);

    // 绑定到video元素
    if (videoRef.value) {
      videoRef.value.srcObject = videoStream.value;
      videoRef.value.onloadedmetadata = () => {
        initCanvas(); // 初始化画布
        startDetectionStream(); // 启动检测循环
        isRunning.value = true;
        isLoading.value = false;
      };
    }
  } catch (error) {
    handleCameraError(error);
    isLoading.value = false;
  }
};

// 停止本地摄像头
const stopLocalCamera = async () => {
  try {
    isLoading.value = true;
    // 停止检测循环
    if (detectionFrameId.value) {
      cancelAnimationFrame(detectionFrameId.value);
      detectionFrameId.value = null;
    }

    // 关闭视频流
    if (videoStream.value) {
      videoStream.value.getTracks().forEach((track) => track.stop());
      videoStream.value = null;
    }

    // 重置状态
    isRunning.value = false;
    isPaused.value = false;
    currentBoxes.value = [];
    frameIndex.value = 0;
    fps.value = 0;
    detectionTime.value = 0;
    totalObjects.value = 0;
    isLoading.value = false;
  } catch (error) {
    ElMessage.error("停止摄像头失败：" + error.message);
    isLoading.value = false;
  }
};

// 暂停/恢复检测
const togglePause = () => {
  isPaused.value = !isPaused.value;
  ElMessage.info(isPaused.value ? "已暂停检测" : "已恢复检测");
};

// 初始化Canvas（和视频尺寸匹配）
const initCanvas = () => {
  if (!videoRef.value || !canvasRef.value || !captureCanvasRef.value) return;

  const video = videoRef.value;
  const canvas = canvasRef.value;
  const captureCanvas = captureCanvasRef.value;

  // 设置Canvas尺寸和视频一致
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  captureCanvas.width = video.videoWidth;
  captureCanvas.height = video.videoHeight;
};

// 启动检测循环
const startDetectionStream = () => {
  const sendFrame = async () => {
    if (!isRunning.value) return;

    const currentTime = performance.now();
    const targetInterval = (inferenceInterval.value * 1000) / 30;

    // 检查元素是否就绪
    if (!videoRef.value || !captureCanvasRef.value) {
      detectionFrameId.value = requestAnimationFrame(sendFrame);
      return;
    }

    // 非暂停且达到检测间隔时执行检测
    if (
      !isPaused.value &&
      currentTime - lastDetectionTime.value >= targetInterval
    ) {
      try {
        const captureCanvas = captureCanvasRef.value;
        const ctx = captureCanvas.getContext("2d");

        // 截取当前视频帧
        ctx.drawImage(
          videoRef.value,
          0,
          0,
          captureCanvas.width,
          captureCanvas.height,
        );

        // 转换为Base64（JPEG压缩，质量0.7）
        const imageData = captureCanvas.toDataURL("image/jpeg", 0.7);

        // 调用后端检测接口
        const response = await detectCameraFrame({ image: imageData });

        if (response.success) {
          // 更新检测结果
          currentBoxes.value = response.data.boxes || [];
          frameIndex.value = response.data.frame_index || frameIndex.value;
          fps.value = response.data.fps || fps.value;
          detectionTime.value = response.data.detection_time || 0;
          totalObjects.value = response.data.total_objects || 0;
          consecutiveErrorCount.value = 0;
          lastDetectionTime.value = currentTime;

          // 绘制检测框
          drawBoxes();
        } else {
          handleDetectionError(response.message);
        }
      } catch (error) {
        handleDetectionError(error.message || "检测请求失败");
      }
    } else if (isPaused.value) {
      // 暂停时只清空检测框
      currentBoxes.value = [];
      drawBoxes();
    }

    // 继续下一帧循环
    detectionFrameId.value = requestAnimationFrame(sendFrame);
  };

  // 启动循环
  detectionFrameId.value = requestAnimationFrame(sendFrame);
};

// 绘制检测框
const drawBoxes = () => {
  if (!canvasRef.value || !videoRef.value) return;

  const canvas = canvasRef.value;
  const ctx = canvas.getContext("2d");
  const video = videoRef.value;

  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 计算缩放比例（适配Canvas和视频尺寸）
  const scaleX = canvas.width / video.videoWidth;
  const scaleY = canvas.height / video.videoHeight;

  // 遍历检测框绘制
  currentBoxes.value.forEach((box) => {
    const x1 = box.x1 * scaleX;
    const y1 = box.y1 * scaleY;
    const x2 = box.x2 * scaleX;
    const y2 = box.y2 * scaleY;
    const width = x2 - x1;
    const height = y2 - y1;

    // 获取类别颜色（可自定义）
    const color = getBoxColor(box.class_name);

    // 绘制边框
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(x1, y1, width, height);

    // 绘制半透明背景
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.1;
    ctx.fillRect(x1, y1, width, height);
    ctx.globalAlpha = 1;

    // 绘制标签
    const label = `${box.chinese_name || box.class_name} ${(box.confidence * 100).toFixed(0)}%`;
    ctx.font = "12px Arial";
    ctx.fillStyle = color;

    const labelWidth = ctx.measureText(label).width + 8;
    const labelHeight = 16;

    // 标签位置（避免超出画面）
    if (y1 >= labelHeight) {
      ctx.fillRect(x1, y1 - labelHeight, labelWidth, labelHeight);
      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, x1 + 4, y1 - 4);
    } else {
      ctx.fillRect(x1, y1 + height, labelWidth, labelHeight);
      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, x1 + 4, y1 + height + 12);
    }
  });
};

// 按类别生成颜色（自定义）
const getBoxColor = (className) => {
  const colorMap = {
    person: "#ff4444",
    car: "#00ff00",
    bicycle: "#0000ff",
    motorcycle: "#ffff00",
    bus: "#ff00ff",
    truck: "#00ffff",
  };
  return (
    colorMap[className] ||
    `#${Math.floor(Math.random() * 16777215).toString(16)}`
  );
};

// 摄像头错误处理
const handleCameraError = (error) => {
  console.error("摄像头错误:", error);
  switch (error.name) {
    case "NotAllowedError":
      ElMessage.error("摄像头权限被拒绝，请在浏览器设置中允许访问");
      break;
    case "NotFoundError":
      ElMessage.error("未检测到摄像头设备，请检查设备连接");
      break;
    case "NotReadableError":
      ElMessage.error("摄像头被其他应用占用，请关闭其他应用后重试");
      break;
    default:
      ElMessage.error("无法访问摄像头：" + error.message);
  }
  stopLocalCamera();
};

// 检测错误处理
const handleDetectionError = (message) => {
  consecutiveErrorCount.value += 1;
  console.error("检测错误:", message);

  // 连续错误超过5次提示
  if (consecutiveErrorCount.value >= 5) {
    ElMessage.error("检测服务异常：" + message);
    consecutiveErrorCount.value = 0;
  }
};

// 组件卸载时清理资源
onUnmounted(() => {
  stopLocalCamera();
});
</script>

<style scoped>
.camera-detection-container {
  max-width: 800px;
  margin: 0 auto;
}

.camera-view-container {
  position: relative;
  border: 1px solid #e6e6e6;
  border-radius: 4px;
  overflow: hidden;
}

.camera-video {
  width: 100%;
  height: auto;
  display: block;
}

.camera-canvas {
  pointer-events: none; /* 避免遮挡视频交互 */
}

.hidden {
  display: none;
}

.mb-4 {
  margin-bottom: 16px;
}

.ml-2 {
  margin-left: 8px;
}

.relative {
  position: relative;
}

.absolute {
  position: absolute;
}

.top-0 {
  top: 0;
}

.left-0 {
  left: 0;
}

.w-32 {
  width: 128px;
}

.w-40 {
  width: 160px;
}

.mt-4 {
  margin-top: 16px;
}
</style>
