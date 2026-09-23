import { createRouter, createWebHashHistory } from 'vue-router'

import ConfigView from '../views/ConfigView.vue'
import ResultView from '../views/ResultView.vue'
import UploadView from '../views/UploadView.vue'

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/upload' },
    { path: '/config', name: 'config', component: ConfigView },
    { path: '/upload', name: 'upload', component: UploadView },
    { path: '/result/:taskId(\\d+)?', name: 'result', component: ResultView, props: true },
  ],
})
