const severityOptions = [
    {name: 'critical', className: 'colored-select-red'},
    {name: 'high', className: 'colored-select-orange'},
    {name: 'medium', className: 'colored-select-yellow'},
    {name: 'low', className: 'colored-select-green'},
    {name: 'info', className: 'colored-select-blue'},
]

const statusOptions = [
    {name: 'valid', className: 'colored-select-red'},
    {name: 'false positive', className: 'colored-select-blue'},
    {name: 'ignored', className: 'colored-select-darkblue'},
    {name: 'not defined', className: 'colored-select-notdefined'},
]

// const ColoredSelect = {
//     delimiters: ['[[', ']]'],
//     props: ['variant', 'initial_value'],
//     // emits: ['update:modelValue'],
//     data() {
//         return {
//             value: undefined,
//             options: [],
//         }
//     },
//     mounted() {
//         this.value = this.initial_value.toLowerCase()
//         switch (this.variant.toLowerCase()) {
//             case 'severity':
//                 this.options = Array.from(severityOptions)
//                 if (~this.options.find(({name}) => name === this.value)) {
//                     console.log('adding new option', this.value)
//                     this.options.push({name: this.value, className: ''})
//                 }
//                 break
//             case 'status':
//                 this.options = statusOptions
//                 if (~this.options.find(({name}) => name === this.value)) {
//                     console.log('adding new option', this.value)
//                     this.options.push({name: this.value, className: ''})
//                 }
//                 break
//             default:
//                 console.warn('Unhandled variant for ColoredSelect: ', this.variant.toLowerCase())
//                 return [{name: this.value, className: ''}]
//         }
//         console.log('cs opts', this.options)
//
//     },
//     template: `
//         <select
//             class="selectpicker btn-colored-select mr-2 btn-colored-table"
//             data-style="btn-colored"
//             v-model="value"
//         >
//             <option
//                 v-for="(item, index) in options"
//                 :class="get_classname(item.name)"
//                 :value="item.name"
//                 :key="index"
//                 style="text-transform: capitalize"
//             >
//                 [[ item.name ]]
//             </option>
//         </select>
//     `,
//     methods: {
//         // onSelectChange(fieldName, value, issueHashes) {
//         //     const data = {
//         //         [fieldName]: value,
//         //         issue_hashes: issueHashes
//         //     }
//         //     fetch(this.url, {
//         //         method: 'PUT',
//         //         body: JSON.stringify(data),
//         //         headers: {'Content-Type': 'application/json'}
//         //     }).then(response => {
//         //         // console.log(response);
//         //         // renderTableFindings();
//         //         this.$emit('rerender')
//         //         // $(document).trigger('updateSummaryEvent');
//         //     })
//         // }
//         get_classname(opt) {
//             const res = this.options.find(({name}) => name === opt)?.className || ''
//             console.log('gettings class for opt', opt, 'res is:', res)
//             return res
//         }
//     }
// }
//
// register_component('ColoredSelect', ColoredSelect)


const TableCardFindings = {
    ...TableCard,
    mounted() {
        console.log('TableCardFindings props', this.$props)
        console.log('TableCardFindings refs', this.$refs)
        // this.$refs.table

        this.url = this.table_url_base

        $(() => {
            $(this.$refs.table).on('all.bs.table', function (e) {
                $('.selectpicker').selectpicker('render')
                initColoredSelect()
            })
            this.rerender()
        })

        this.register_formatters()

        this.fetchFilters()
        // this.initTable()

    },
    // components: {
    //     'report-filter': ReportFilter,
    //     'choose-filter': ChooseFilter,
    //     'modal-save-filter': modalSaveFilter,
    // },
    data() {
        return {
            ...TableCard.data(),
            url: undefined,
            status_map: {
                all: '',
                valid: 'valid',
                'false positive': 'false_positive',
                ignored: 'ignored'
            },
            showModal: false,
            filtersName: [],
            loadingSave: false,
            loadingSaveAs: false,
            loadingApply: false,
            filters: null,
            selectedFilter: null,
            loadingFilters: false,
            loadingDelete: false,
            updatedFilter: null,
            // tableData,
        }
    },
    methods: {
        ...TableCard.methods,
        rerender() {
            this.table_action('refresh', {
                url: this.url.href,
            })
        },
        clear_search_params() {
            this.url.searchParams.forEach((v, k) => this.url.searchParams.delete(k))
        },
        ping(some_v) {
            console.log('ping', some_v)
        },
        handle_status_filter(status) {
            this.clear_search_params()
            this.url.searchParams.set('status', this.status_map[status.toLowerCase()] || '')
            this.rerender()
        },
        register_formatters() {
            const selectpicker_formatter = opts => ((value, row, index, field) => {
                let options = opts.reduce((accum, {name, className},) =>
                        `${accum}<option
                        class="text-uppercase ${className}"
                        value='${name}'
                        ${name.toLowerCase() === value.toLowerCase() && 'selected'}
                    >
                        ${name}
                    </option>
                    `,
                    ''
                )
                const to_add_unexpected_value = opts.find(
                    item => item.name.toLowerCase() === value.toLowerCase()
                ) === undefined

                options += to_add_unexpected_value ? `<option value="${value}" selected>${value}</option>` : ''

                return `
                    <select
                        class="selectpicker btn-colored-select"
                        data-style="btn-colored"
                        value="${value}"
                        data-field="${field}"
                    >
                        ${options}
                    </select>
                `
            })
            window.findings_formatter_severity = selectpicker_formatter(severityOptions)
            window.findings_formatter_status = selectpicker_formatter(statusOptions)
            window.findings_eventhandler = {
                'change .selectpicker': this.handleSelectpickerChange
            }

            window.findings_formatter_details = ((index, row) => `
                <div class="col ml-3">
                    <div class="details_view">
                        <p><b>Issue Details:</b></p> ${row['details']} <br />
                    </div>
                </div>
            `)
        },
        handleSelectpickerChange(event, value, row, index) {
            // I'll leave this func here as it may be useful somewhere
            // const get_col_name = el => {
            //     const td = $(el).closest('td')
            //     const col_num = td.parent().children().index(td)
            //     return $(el).closest('table').find('thead tr').children(`:eq(${col_num})`).text().trim().toLowerCase()
            // }

            this.handleModify({
                issue_hashes: [row.issue_hash],
                [event.target.dataset.field]: event.target.value
            })
        },
        handleModify(data) {
            // const data = {
            //     issue_hashes: issueHashes,
            //     [dataType]: value
            // }
            fetch(this.url, {
                method: 'PUT',
                body: JSON.stringify(data),
                headers: {'Content-Type': 'application/json'}
            }).then(response => {
                this.rerender()
                $(document).trigger('updateSummaryEvent')
            })
        },
        bulkModify(dataType, value) {
            const issueHashes = this.table_action('getSelections').map(item => item.issue_hash)
            if (issueHashes.length > 0) {
                const data = {
                    issue_hashes: issueHashes,
                    [dataType]: value
                }
                this.handleModify(data)
            }
        },
        // initTable() {
        //     const tableOptions = {
        //         columns: tableColumns,
        //         data: this.tableData,
        //         theadClasses: 'thead-light'
        //     }
        //     $('#table').bootstrapTable(tableOptions)
        // },
        fetchFilters() {
            // this.loadingFilters = true;
            // apiFetchFilters.then(res => {
            //     this.filters = res;
            // }).finally(() => {
            //     this.loadingFilters = false;
            // })
        },
        // updateTable(filterSetting) {
        //     this.loadingApply = true;
        //     $('#table').bootstrapTable('destroy');
        //     setTimeout(() => {
        //         console.log('SETTING FOR SERVER:', filterSetting.options)
        //         apiFetchTable.then(response => {
        //             const {columns, data} = response;
        //             const tableOptions = {
        //                 columns,
        //                 data,
        //                 theadClasses: 'thead-light'
        //             }
        //             $('#table').bootstrapTable(tableOptions);
        //             $('.selectpicker').selectpicker('render');
        //         }).finally(() => {
        //             this.loadingApply = false;
        //         })
        //     }, 500)
        // },
        createFilter() {
            this.selectedFilter = {
                id: null,
                title: '',
                options: [
                    {
                        id: Math.round(Math.random() * 1000),
                        column: '',
                        operator: '',
                        title: '',
                    }
                ]
            }
        },
        selectFilter(filter) {
            this.selectedFilter = filter;
        },
        setFilters(filters) {
            this.filtersName = filters.map(filter => filter.title);
        },
        openModal() {
            this.showModal = !this.showModal;
        },
        saveFilterAs(createdFilter) {
            this.filters.push(createdFilter);
            this.openModal();
        },
        saveFilter(currentFilter) {
            // this.loadingSave = true;
            // setTimeout(() => {
            //     apiSaveFilter(currentFilter).then(response => {
            //         this.selectFilter(response.data);
            //         showNotify('SUCCESS', response.message);
            //         this.fetchFilters();
            //     }).catch(error => {
            //         showNotify('ERROR', error);
            //     }).finally(() => {
            //         this.loadingSave = false;
            //     })
            // }, 500)
        },
        saveNewFilter(filterName) {
            // this.loadingSaveAs = true;
            // setTimeout(() => {
            //     apiSaveAsFilter(this.updatedFilter, filterName).then(response => {
            //         this.selectFilter(response.data);
            //         showNotify('SUCCESS', response.message);
            //         this.openModal();
            //         this.fetchFilters();
            //     }).catch(error => {
            //         showNotify('ERROR', error);
            //     }).finally(() => {
            //         this.loadingSaveAs = false;
            //     })
            // }, 500)
        },
        updateCurentFilter(updatedFilter) {
            this.updatedFilter = deepClone(updatedFilter);
        },
        deleteFilter(filter) {
            // this.loadingDelete= true;
            // setTimeout(() => {
            //     apiDeleteFilter(filter).then((response) => {
            //         showNotify('SUCCESS', response.message);
            //         this.fetchFilters();
            //     }).finally(() => {
            //         this.loadingDelete = false;
            //     })
            // }, 500);
        }
    },
    computed: {
        ...TableCard.computed,
        table_url_base() {
            const result_test_id = new URLSearchParams(location.search).get('result_id')
            let url = new URL(`/api/v1/security/findings/${getSelectedProjectId()}/${result_test_id}/`, location.origin)
            return url
        },
    }

}

register_component('TableCardFindings', TableCardFindings)

