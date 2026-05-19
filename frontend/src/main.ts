import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { ElMessageBox } from 'element-plus'
import router from './router'
import './assets/styles/premium-dark.css'
import './assets/styles/themes.css'
import './components/common/modal/modalTokens.css'
import './assets/styles/readability.css'
import App from './App.vue'
import CyberToast from './components/common/CyberToast.vue'
import CyberConfirm from './components/common/CyberConfirm.vue'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.component('CyberToast', CyberToast)
app.component('CyberConfirm', CyberConfirm)
app.config.globalProperties.$msgbox = ElMessageBox
app.mount('#app')
