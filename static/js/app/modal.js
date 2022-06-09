class SectionDataProvider {
    static allowed_methods = ['get', 'set', 'clear', 'setError', 'clearErrors']

    constructor(name, actions) {
        this.name = name
        SectionDataProvider.allowed_methods.forEach(
            item => this[item] = actions[item] || SectionDataProvider.not_defined(name, item)
        )
    }

    static not_defined = (provider, method_name) => () => {
        console.warn(`Method ${method_name} is not defined for ${provider}`)
    }
    register = () => SecurityModal._instance ?
        SecurityModal._instance.registerDataProvider(this) :
        console.warn('SecurityModal instance not declared')
}

// SecurityModal is a singleton for a security modal with test creation functionality.
// to add a new section register it with help of SectionDataProvider(...).register()
class SecurityModal {
    static _instance = null
    test_uid = null
    dataModel = {}

    constructor(containerId) {
        if (SecurityModal._instance) {
            return SecurityModal._instance
        }
        this.containerId = containerId
        this.refreshContainer()
        SecurityModal._instance = this
        this.registerDataProvider(new SectionDataProvider('name', {
            get: () => $('#test_name').val(),
            set: value => $('#test_name').val(value),
            clear: () => $('#test_name').val(''),
            setError: data => $('#test_name').addClass('is-invalid').next('div.invalid-feedback').text(data.msg),
            clearErrors: () => $('#test_name').removeClass('is-invalid')
        }))
        this.registerDataProvider(new SectionDataProvider('description', {
            get: () => $('#test_description').val(),
            set: value => $('#test_description').val(value),
            clear: () => $('#test_description').val(''),
        }))
        this.registerDataProvider(new SectionDataProvider('test_parameters', {
            get: () => $('#security_test_params').bootstrapTable('getData'),
            set: (urls_to_scan, urls_exclusions, scan_location, test_parameters = []) => {
                console.debug('SET test_parameters', urls_to_scan, urls_exclusions, scan_location, test_parameters)
                const table_data = [
                    {
                        default: urls_to_scan.join(','),
                        description: "Data",
                        name: "URL to scan",
                        type: "List[URL]",
                        _description_class: "disabled",
                        _name_class: "disabled",
                        _type_class: "disabled",
                    },
                    {
                        default: urls_exclusions?.join(','),
                        description: "Data",
                        name: "Exclusions",
                        type: "List[URL]",
                        _description_class: "disabled",
                        _name_class: "disabled",
                        _type_class: "disabled",
                    },
                    {
                        default: scan_location,
                        description: "Data",
                        name: "Scan location",
                        type: "String",
                        _description_class: "disabled",
                        _name_class: "disabled",
                        _type_class: "disabled",
                    },
                    ...test_parameters.filter(item => !['url to scan', 'exclusions', 'scan location'].includes(item.name))
                ]
                $('#security_test_params').bootstrapTable('load', table_data)
            },
            clear: () => {
                console.debug('CLEAR test_parameters')
                const table_data = [
                    {
                        default: '',
                        description: "Data",
                        name: "URL to scan",
                        type: "List[URL]",
                        _description_class: "disabled",
                        _name_class: "disabled",
                        _type_class: "disabled",
                    },
                    {
                        default: '',
                        description: "Data",
                        name: "Exclusions",
                        type: "List[URL]",
                        _description_class: "disabled",
                        _name_class: "disabled",
                        _type_class: "disabled",
                    },
                    {
                        default: '',
                        description: "Data",
                        name: "Scan location",
                        type: "String",
                        _description_class: "disabled",
                        _name_class: "disabled",
                        _type_class: "disabled",
                    }
                ]
                $('#security_test_params').bootstrapTable('load', table_data)
            },
            setError: data => {
                console.debug('SET error test_parameters', data)
                const get_col_by_name = name => $(`#security_test_params thead th[data-field=${name}]`).index()
                const [_, row, col_name] = data.loc
                $(`#security_test_params tr[data-index=${row}] td:nth-child(${get_col_by_name(col_name) + 1}) input`)
                    .addClass('is-invalid')
                    .next('div.invalid-tooltip-custom')
                    .text(data.msg)

            },
            clearErrors: () => $('#security_test_params').removeClass('is-invalid')
        }))
        this.registerDataProvider(new SectionDataProvider('alert_bar', {
            clear: () => alertCreateTest?.clear(),
            setError: data => alertCreateTest?.add(data.msg, 'dark-overlay', true)
        }))
    }

    refreshContainer = () => {
        this.container = $(`#${this.containerId}`)
        this.container.on('hide.bs.modal', this.clear)
    }

    registerDataProvider = provider => this.dataModel[provider.name] = provider

    setData = data => {
        console.debug('SecurityModal SET data', data)
        const {
            urls_to_scan, urls_exclusions, scan_location, test_parameters,
            test_uid,
            ...rest
        } = data
        this.test_uid = test_uid
        Object.entries(rest).forEach(([k, v]) => this.dataModel[k]?.set(v))
        this.dataModel.test_parameters?.set(urls_to_scan, urls_exclusions, scan_location, test_parameters)

    }
    clear = () => {
        Object.keys(this.dataModel).forEach(item => {
            this.dataModel[item].clear()
        })
        $('#modal_title').text('Add Application Test')
        $('#security_test_save').text('Save')
        $('#security_test_save_and_run').text('Save And Start')
        this.test_uid = null
        this.clearErrors()
    }
    collectData = () => {
        let data = {}
        Object.entries(this.dataModel).forEach(([k, v]) => {
            data[k] = v.get()
        })
        return data
    }

    setValidationErrors = errorData => {
        errorData?.forEach(item => {
            const [errLoc, ...rest] = item.loc
            item.loc = rest
            this.dataModel[errLoc]?.setError(item)
        })
        alertCreateTest?.add('Please fix errors below', 'danger', true, 5000)
    }

    clearErrors = () => {
        // this.container.find('input.is-invalid').removeClass('is-invalid')
        // this.container.find('.invalid-feedback').text('')
        // this.container.find('.invalid-tooltip').text('')
        Object.keys(this.dataModel).forEach(item => this.dataModel[item].clearErrors())
    }

    handleSave = () => {
        const data = this.collectData()
        if (!this.test_uid) {
            console.log('Creating test with data', data)
            apiActions.create(data)
        } else {
            console.log('Editing test with data', data)
            apiActions.edit(this.test_uid, data)
        }

    }
    handleSaveAndRun = () => {
        const data = this.collectData()
        if (!this.test_uid) {
            console.log('Creating and running test with data', data)
            apiActions.createAndRun(data)
        } else {
            console.log('Editing and running test with data', data)
            apiActions.editAndRun(this.test_uid, data)
        }
    }

}

var securityModal = new SecurityModal('createApplicationTest')
// wait_for('vueVm').then(() => {
//     securityModal.refreshContainer()
// })

$(document).on('vue_init', () => {
    securityModal.refreshContainer()
    $('#security_test_save').on('click', securityModal.handleSave)
    $('#security_test_save_and_run').on('click', securityModal.handleSaveAndRun)
})