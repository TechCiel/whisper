byId = document.getElementById.bind(document)

done = {}

function try_auth(name) {
    done[name] = true
    for (criteria of policy) {
        fulfilled = true
        for (method of criteria) {
            fulfilled = fulfilled && (method in done)
        }
        if (fulfilled) {
            byId('auth').submit()
            break
        }
    }
}
