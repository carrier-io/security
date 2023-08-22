var tableFormatters = {
    reports_test_name_button(value, row, index) {
        return `<a href="./results?result_id=${row.id}" role="button">${row.name}</a>`
    },
    reports_status_formatter(value, row, index) {
        switch (value.toLowerCase()) {
            case 'error':
            case 'failed':
                return `<div style="color: var(--red)">${value} <i class="fas fa-exclamation-circle error"></i></div>`
            case 'stopped':
                return `<div style="color: var(--yellow)">${value} <i class="fas fa-exclamation-triangle"></i></div>`
            case 'aborted':
                return `<div style="color: var(--gray)">${value} <i class="fas fa-times-circle"></i></div>`
            case 'finished':
                return `<div style="color: var(--info)">${value} <i class="fas fa-check-circle"></i></div>`
            case 'passed':
                return `<div style="color: var(--green)">${value} <i class="fas fa-check-circle"></i></div>`
            case 'pending...':
                return `<div style="color: var(--basic)">${value} <i class="fas fa-spinner fa-spin fa-secondary"></i></div>`
            default:
                return value
        }
    },
    tests_actions(value, row, index) {
        return `
            <div class="d-flex justify-content-end">
                <button type="button" class="btn btn-24 btn-action" id="test_run"><i class="fas fa-play"></i></button>
                <div class="dropdown_multilevel">
                    <button class="btn btn-24 btn-action" type="button"
                            data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                    <ul class="dropdown-menu">
                        <!--<li class="dropdown-menu_item dropdown-item d-flex align-items-center">
                            <span class="w-100 font-h5"><i class="fas fa-share-alt mr-2"></i>Integrate with</span>
                            <i class="fa fa-sort-down"
                               style="transform: rotate(270deg)"
                            ></i>
                            <ul class="submenu dropdown-menu">
                                <li class="dropdown-menu_item dropdown-item d-flex align-items-center">
                                    <span class="w-100 font-h5">Docker command</span>
                                </li>
                                <li class="dropdown-menu_item dropdown-item d-flex align-items-center">
                                    <span class="w-100 font-h5">Jenkins stage</span>
                                </li>
                                <li class="dropdown-menu_item dropdown-item d-flex align-items-center">
                                    <span class="w-100 font-h5">Azure DevOps yaml</span>
                                </li>
                                <li class="dropdown-menu_item dropdown-item d-flex align-items-center">
                                    <span class="w-100 font-h5">Test UID</span>
                                </li>
                            </ul>
                        </li>-->
                        <li class="dropdown-menu_item dropdown-item d-flex align-items-center"
                            id="test_settings"
                        >
                            <i class="fas fa-cog mr-2"></i><span class="w-100 font-h5">Settings</span>
                        </li>
                        <li class="dropdown-menu_item dropdown-item d-flex align-items-center"
                            id="test_delete"
                        >
                            <i class="fas fa-trash-alt mr-2"></i><span class="w-100 font-h5">Delete</span>
                        </li>
                    </ul>
                </div>

            </div>
        `
    },
    tests_tools(value, row, index) {
        // todo: fix
        return Object.keys(value?.scanners || {})
    },
    application_urls(value, row, index) {
        const enable_tooltip = JSON.stringify(value).length > 42  // because 42
        return `<div
                    style="
                        max-width: 240px;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                        overflow: hidden;
                    "
                    ${enable_tooltip && 'data-toggle="infotip"'}
                    data-placement="top"
                    title='${value}'
                >${value}</div>`
    },
    status_events: {
        "click #test_run": function (e, value, row, index) {
            apiActions.run(row.id, row.name)
        },

        "click #test_settings": function (e, value, row, index) {
            securityModal.setData(row)
            securityModal.container.modal('show')
            $('#modal_title').text('Edit Application Test')
            $('#security_test_save').text('Update')
            $('#security_test_save_and_run').text('Update And Start')

        },

        "click #test_delete": function (e, value, row, index) {
            apiActions.delete(row.id)
        }
    }
}

var apiActions = {
    base_url: api_name => `/api/v1/security/${api_name}/${getSelectedProjectId()}`,
    run: (id, name) => {
        fetch(`${apiActions.base_url('test')}/${id}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({'test_name': name})
        }).then(response => response.ok && apiActions.afterSave())
    },
    delete: ids => {
        const url = `${apiActions.base_url('tests')}?` + $.param({"id[]": ids})
        fetch(url, {
            method: 'DELETE'
        }).then(response => response.ok && apiActions.afterSave())
    },
    edit: (testUID, data) => {
        apiActions.beforeSave()
        fetch(`${apiActions.base_url('test')}/${testUID}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        }).then(response => {
            apiActions.afterSave()
            if (response.ok) {
                securityModal.container.modal('hide');
            } else {
                response.json().then(data => securityModal.setValidationErrors(data))
            }
        })
    },
    editAndRun: (testUID, data) => {
        data['run_test'] = true
        return apiActions.edit(testUID, data)
    },
    create: data => {
        apiActions.beforeSave()
        fetch(apiActions.base_url('tests'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        }).then(response => {
            apiActions.afterSave()
            if (response.ok) {
                $("#createApplicationTest").modal('hide');
            } else {
                response.json().then(data => securityModal.setValidationErrors(data))
            }
        })
    },
    createAndRun: data => {
        data['run_test'] = true
        return apiActions.create(data)
    },
    beforeSave: () => {
        $("#security_test_save").addClass("disabled updating")
        $("#security_test_save_and_run").addClass("disabled updating")
        securityModal.clearErrors()
        alertCreateTest?.clear()
    },
    afterSave: () => {
        $("#application_tests_table").bootstrapTable('refresh')
        $("#results_table").bootstrapTable('refresh')
        $("#security_test_save").removeClass("disabled updating")
        $("#security_test_save_and_run").removeClass("disabled updating")
    },
    results_delete: ids => {
        const url = `${apiActions.base_url('results')}?` + $.param({"id[]": ids})
        fetch(url, {
            method: 'DELETE'
        }).then(response => response.ok && vueVm.registered_components.table_results?.table_action('refresh'))
    },

}

function testQueryParams(params){
    const urlSearchParams = new URLSearchParams(window.location.search);
    const currentParams = Object.fromEntries(urlSearchParams.entries());
    params['filter'] = JSON.stringify({'test_uid': currentParams['test_uid']})
    return params
}

function testResultsqueryParams(params){
    const urlSearchParams = new URLSearchParams(window.location.search);
    const currentParams = Object.fromEntries(urlSearchParams.entries());
    params['filter'] = JSON.stringify(currentParams)
    return params
}

$(document).on('vue_init', () => {
    $('#delete_test').on('click', e => {
        const ids_to_delete = $(e.target).closest('.card').find('table.table').bootstrapTable('getSelections').map(
            item => item.id
        ).join(',')
        ids_to_delete && apiActions.delete(ids_to_delete)
    })

    $('#delete_results').on('click', e => {
        const ids_to_delete = vueVm.registered_components.table_results?.table_action('getSelections').map(
            item => item.id
        ).join(',')
        ids_to_delete && apiActions.results_delete(ids_to_delete)
    })

    $("#application_tests_table").on('all.bs.table', initTooltips)
})
