var tableFormatters = {
    reports_test_name_button(value, row, index) {
        // const searchParams = new URLSearchParams(location.search);
        // searchParams.set('module', 'Result');
        // searchParams.set('page', 'list');
        // searchParams.set('project_id', getSelectedProjectId());
        // searchParams.set('result_test_id', row.id);
        // searchParams.set('test_id', row.test_id);
        // return `<a class="test form-control-label" href="?${searchParams.toString()}" role="button">${row.name}</a>`
        return `<a class="test form-control-label" href="./results?result_id=${row.id}" role="button">${row.name}</a>`
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
                <button type="button" class="btn btn-24 btn-action run"><i class="fas fa-play"></i></button>
                <div class="dropdown action-menu">
                    <button type="button" class="btn btn-24 btn-action" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                    <div class="dropdown-menu bulkActions" aria-labelledby="bulkActionsBtn">
                        <a class="dropdown-item submenu" href="#"><i class="fas fa-share-alt fa-secondary fa-xs"></i> Integrate with</a>
                        <div class="dropdown-menu">
                            <a class="dropdown-item" href="#" onclick="console.log('Docker command')">Docker command</a>
                            <a class="dropdown-item" href="#" onclick="console.log('Jenkins stage')">Jenkins stage</a>
                            <a class="dropdown-item" href="#" onclick="console.log('Azure DevOps yaml')">Azure DevOps yaml</a>
                            <a class="dropdown-item" href="#" onclick="console.log('Test UID')">Test UID</a>
                        </div>
                        <a class="dropdown-item settings" href="#"><i class="fas fa-cog fa-secondary fa-xs"></i> Settings</a>
                        <a class="dropdown-item trash" href="#"><i class="fas fa-trash-alt fa-secondary fa-xs"></i> Delete</a>
                    </div>
                </div>
            </div>
        `
    },
    tests_tools(value, row, index) {
        // todo: fix
        return Object.keys(value?.scanners || {})
    },
    status_events: {
        "click .run": function (e, value, row, index) {
            apiActions.run(row.id, row.name)
        },

        "click .settings": function (e, value, row, index) {
            securityModal.setData(row)
            securityModal.container.modal('show')
            $('#modal_title').text('Edit Application Test')
            $('#security_test_save').text('Update')
            $('#security_test_save_and_run').text('Update And Start')

        },

        "click .trash": function (e, value, row, index) {
            apiActions.delete(row.id)
        }
    }
}

var apiActions = {
    base_url: api_name => `/api/v1/security/${api_name}/${getSelectedProjectId()}`,
    run: (id, name) => {
        console.log('Run test', id)
        fetch(`${apiActions.base_url('test')}/${id}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({'test_name': name})
        }).then(response => response.ok && apiActions.afterSave())
    },
    delete: ids => {
        const url = `${apiActions.base_url('tests')}` + $.param({"id[]": ids})
        console.log('Delete test with id', ids, url);
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
        $("#tests-list").bootstrapTable('refresh')
        $("#results-list").bootstrapTable('refresh')
        $("#security_test_save").removeClass("disabled updating")
        $("#security_test_save_and_run").removeClass("disabled updating")
    },


}


$(document).on('vue_init', () => {
    $('#delete_test').on('click', e => {
        console.log('e', $(e.target).closest('.card').find('table.table'))
        const ids_to_delete = $(e.target).closest('.card').find('table.table').bootstrapTable('getSelections').map(
            item => item.id
        ).join(',')
        ids_to_delete && apiActions.delete(ids_to_delete)
    })
})
