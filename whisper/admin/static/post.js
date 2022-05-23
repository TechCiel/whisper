byId = document.getElementById.bind(document)

byId('new_meta').addEventListener('change', function autoMeta(e) {
    if (byId('new_meta').value) {
        old_key = byId('new_meta')
        old_value = old_key.parentElement.nextElementSibling.firstElementChild
        old_tr = old_key.parentElement.parentElement

        new_tr = old_tr.cloneNode(true)
        new_tr.firstElementChild.firstElementChild.value = ''
        new_tr.lastElementChild.firstElementChild.value = ''

        old_key.id = ''
        old_key.removeEventListener('change', autoMeta)

        old_tr.parentElement.appendChild(new_tr)
        new_tr.firstElementChild.firstElementChild.addEventListener('change', autoMeta)
    }
})

unsaved = false;

document.querySelectorAll('[form="post"]').forEach((ele) => {
    ele.addEventListener('change', () => {
        unsaved = true
    })
})

function checkUnsaved() {
    if (unsaved) alert('Please save post first!')
    return !unsaved
}

function deleteFile(node) {
    if (!checkUnsaved()) return false
    byId('delete-name').value = node.previousElementSibling.text
    if (confirm('Are you sure?')) byId('delete').submit()
}
