import type { Strategy } from '../recovery_strategies_types';
// Единственный источник карточек: локальные mock-объекты. Нет fetch, axios, API, БД или S3.
export const mockStrategies: Strategy[] = [
 {id:1,title:'Синхронная репликация',short_description:'Мгновенная репликация данных с минимальным временем восстановления.',status:'published',image_url:'/media/recovery_strategies_sync_image.png',video_url:'/media/recovery_strategies_sync_video.mp4',estimated_time:15,cost:1500,likes_count:3},
 {id:2,title:'Асинхронная репликация',short_description:'Репликация с небольшим отставанием для удалённой площадки.',status:'published',image_url:'/media/recovery_strategies_async_image.png',video_url:'/media/recovery_strategies_async_video.mp4',estimated_time:45,cost:800,likes_count:7},
 {id:3,title:'Холодное резервирование',short_description:'Восстановление сервиса из резервной копии после сбоя.',status:'published',image_url:'/media/recovery_strategies_cold_image.png',video_url:'/media/recovery_strategies_cold_video.mp4',estimated_time:240,cost:250,likes_count:2},
 {id:4,title:'Облачное восстановление',short_description:'Восстановление инфраструктуры на облачной площадке.',status:'published',image_url:'/media/recovery_strategies_cloud_image.png',video_url:'/media/recovery_strategies_cloud_video.mp4',estimated_time:90,cost:1200,likes_count:5},
 {id:5,title:'Резервное копирование БД',short_description:'Восстановление базы данных из регулярных резервных копий.',status:'published',image_url:null,video_url:null,estimated_time:100,cost:200,likes_count:1},
 {id:6,title:'Аварийное восстановление файлов',short_description:'Возврат важных файлов после сбоя хранилища.',status:'published',image_url:null,video_url:null,estimated_time:180,cost:500,likes_count:0},
];
