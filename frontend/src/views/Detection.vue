<template>
  <div>
    <h2>遥感图像智能检测</h2>
    <br/>

    <!-- 并排对比 -->
    <div v-if="compareMode === 'side'" class="side-by-side">
      <div class="image-card">
        <h4>原图</h4>
        <img :src="originalImage" alt="原图" />
      </div>
      <div class="image-card">
        <h4>AI标注结果</h4>
        <img :src="annotatedImage" alt="标注图" />
      </div>
    </div>

    <!-- 滑块对比 -->
    <div v-if="compareMode === 'slider'" class="slider-container">
      <SliderCompare
        :before="originalImage"
        :after="annotatedImage"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SliderCompare from '../components/SliderCompare.vue'

const compareMode = ref('side')
const originalImage = ref('')
const annotatedImage = ref('')
</script>

<style scoped>
.side-by-side {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
}
.image-card {
  width: 45%;
}
.image-card img {
  width: 100%;
  border-radius: 8px;
  margin-top: 10px;
}
</style>