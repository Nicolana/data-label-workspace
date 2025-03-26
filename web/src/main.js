import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 引入 md-editor-v3 编辑器
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'

const app = createApp(App)
app.use(ElementPlus)
app.component('MdEditor', MdEditor)
app.mount('#app')