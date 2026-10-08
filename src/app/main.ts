import { createApp } from 'vue';
import { createPinia } from 'pinia';
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';
import '@/app/styles/main.scss';

import App from './App.vue';
import { useFundStore } from '@/entities/fund/model/fundStore';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(Antd);

app.mount('#app');

void useFundStore().initializeFromApi();
