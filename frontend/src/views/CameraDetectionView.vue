<template>
  <div class="camera-detection-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="breadcrumb">
        <span>工作台</span>
        <span class="separator">›</span>
        <span class="active">摄像头检测</span>
      </div>
      <h1 class="page-title">实时摄像头目标检测</h1>
      <p class="page-subtitle">
        开启摄像头，实时检测视频流中的目标物体
      </p>
    </div>

    <!-- 摄像头检测组件 -->
    <CameraDetection />
  </div>
</template>

<script setup>
import CameraDetection from "../components/CameraDetection.vue";
</script>

<style scoped>
.camera-detection-view {
  width: 100%;
}

.page-header {
  margin-bottom: 24px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #666;
}

.separator {
  color: #ccc;
}

.active {
  color: #aa3bff;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #08060d;
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 14px;
  color: #666;
}
</style>