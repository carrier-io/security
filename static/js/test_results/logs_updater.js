const LogsApp = {
    data() {
        return {
            state: 'unknown',
            websocket: undefined,
            connection_retries: 5,
            connection_retry_timeout: 2000,
            logs: []
        }

    },
    mounted() {

    },
    // updated() {
    //     var item = $("#logs-body");
    //     item.scrollTop(item.prop("scrollHeight"));
    // },
    computed: {
        reversedLogs: function () {
            return this.logs.reverse()
        },
        page_params: () => new URLSearchParams(location.search),
        test_id: () => this.page_params.get('test_id'),
        project_id: () => this.page_params.get('project_id'),
        result_test_id: () => this.page_params.get('result_test_id'),
        websocket_api_url: () => `/api/v1/security/loki_url/${project_id}/?task_id=${test_id}&result_test_id=${result_test_id}`
    },
    template: `
        <div class="card card-12 mb-5">
            <div class="card-header">
                <div class="row">
                    <div class="col-2"><h3>Logs</h3></div>
                </div>
            </div>
            <div class="card-body card-table">
              <div id="logs-body" class="card-body overflow-auto pt-0 pl-3">
                  <ul class="list-group">
                      <li v-for="line in reversedLogs" class="list-group-item">
                          <div style="word-break: break-all; white-space: pre-wrap;">[[ line ]]</div>
                      </li>
                  </ul>
              </div>
            </div>
        </div>
    `,
    methods: {
        init_websocket() {
            fetch(this.websocket_api_url, {
                method: 'GET'
            }).then(response => {
                if (response.ok) {
                    this.websocket = new WebSocket(data['websocket_url'])
                    this.websocket.onmessage = this.on_websocket_message
                    this.websocket.onopen = this.on_websocket_open
                    this.websocket.onclose = this.on_websocket_close
                    this.websocket.onerror = this.on_websocket_error
                } else {
                    console.warn('Websocket failed to initialize', response)
                }
            })
        },
        on_websocket_open(message) {
            this.state = 'connected'
        },
        on_websocket_message(message) {
            if (message.type !== 'message') {
                console.log('Unknown message', message)
                return
            }

            const data = JSON.parse(message.data)

            data.streams.forEach(stream_item => {
                stream_item.values.forEach(message_item => {
                    this.logs.push(`${stream_item.stream.level} : ${message_item[1]}`)
                })
            })
        },
        on_websocket_close(message) {
            this.state = 'disconnected'
            let attempt = 1;
            const intrvl = setInterval(() => {
                this.init_websocket()
                if (this.state === 'connected' || attempt > this.connection_retries) clearInterval(intrvl)
                attempt ++
            }, this.connection_retry_timeout)
            // setTimeout(websocket_connect, 1 * 1000);
            //    clearInterval(websocket_connect)
        },
        on_websocket_error(message) {
            this.state = 'error'
            this.websocket.close()
        }

    }
}

Vue.createApp({
    components: LogsApp
}).mount('#logs')
