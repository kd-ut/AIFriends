const HTTP_URL = 'http://127.0.0.1:8000'

const CONFIG_API = {
    HTTP_URL,
    VAD_URL: import.meta.env.DEV
        ? `${window.location.origin}/vad-runtime/`
        : 'http://127.0.0.1:8000/static/frontend/vad-runtime-v2/',
}

export default CONFIG_API
