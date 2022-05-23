byId = document.getElementById.bind(document)

pageUpdate = false

function update() {
    var query = new URLSearchParams();
    ['visible', 'index', 'tag', 'search', 'provide', 'page'].forEach((id) => {
        value = byId(id).value
        if (value !== '') query.set(id, value)
    })
    if (!pageUpdate || query.get('page') === '1') query.delete('page')
    window.location.search = query.toString()
}

function setUpdate(id, value) {
    byId(id).value = value
    update()
}

function page(page) {
    pageUpdate = true
    setUpdate('page', page)
}