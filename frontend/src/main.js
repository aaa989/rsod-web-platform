import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'   // 引⼊路由
const app = createApp(App)
app.use(router)   // 启⽤路由
app.mount('#app')