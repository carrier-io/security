// page_params = page_params || new URLSearchParams(location.search);

const getTableUrlArtifacts = () => {
    const result_test_id = new URLSearchParams(location.search).get('result_id')
    return `/api/v1/artifacts/security_results/${result_test_id}/`
}
const getTableUrlDownloadArtifacts = () => {
    const result_test_id = new URLSearchParams(location.search).get('result_id')
    return `/api/v1/artifacts/security_download/${result_test_id}`
}

function renderTableArtifacts() {
    $("#artifacts").bootstrapTable('refresh', {
        url: getTableUrlArtifacts(),
    })
}

function artifactActionsFormatter(value, row, index) {return _artifactActionsFormatter(value, row, index)}

const _artifactActionsFormatter = (value, row, index) => {
    return `<a href="${getTableUrlDownloadArtifacts()}/${row['name']}" class="fa fa-download btn-action" download="${row['name']}"></a>`
}

// $.when( $.ready ).then(function() {
//   renderTableArtifacts()
// });

$(document).on('vue_init', () => renderTableArtifacts())